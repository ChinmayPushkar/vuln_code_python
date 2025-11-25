import logging
from subprocess import CalledProcessError
import tarfile
import json
import os
import shutil
import subprocess
import traceback
from abc import ABCMeta
from ast import literal_eval
from copy import copy, deepcopy
from grp import getgrnam
from hashlib import md5, sha1
from importlib.machinery import SourceFileLoader
from os.path import commonprefix, isdir, isfile, join
from pwd import getpwnam
from random import randint, Random
from time import sleep
from urllib.parse import unquote

from hacksport.operations import create_user, execute
from hacksport.problem import (
    Compiled,
    Directory,
    ExecutableFile,
    File,
    FlaskApp,
    GroupWriteDirectory,
    PHPApp,
    WebService,
    PreTemplatedFile,
    ProtectedFile,
    Remote,
    Service,
)
from hacksport.docker import DockerChallenge
from hacksport.status import get_all_problem_instances, get_all_problems
from jinja2 import Environment, FileSystemLoader, Template
from shell_manager.package import package_problem
from shell_manager.util import (
    DEPLOYED_ROOT,
    FatalException,
    get_attributes,
    get_problem,
    get_problem_root,
    sanitize_name,
    STAGING_ROOT,
    get_problem_root_hashed,
    get_pid_hash,
    get_bundle,
    DEB_ROOT,
    SHARED_ROOT,
    get_shared_config,
    get_local_config,
    acquire_lock,
    release_lock,
)
from spur import RunProcessError

PORT_MAP_PATH = join(SHARED_ROOT, "port_map.json")

def challenge_meta(attributes):
    class ChallengeMeta(ABCMeta):
        def __new__(cls, name, bases, attr):
            attrs = dict(attr)
            attrs.update(attributes)
            return super().__new__(cls, name, bases, attrs)
    return ChallengeMeta

def update_problem_class(Class, problem_object, seed, user, instance_directory):
    random = Random(seed)
    attributes = deepcopy(problem_object)
    attributes.update(dict(shared_config))
    attributes.update(dict(local_config))
    attributes.update({
        "random": random,
        "user": user,
        "directory": instance_directory,
        "server": local_config.hostname,
    })
    return challenge_meta(attributes)(Class.__name__, Class.__bases__, Class.__dict__)

def get_username(problem_name, instance_number):
    username = "{}_{}".format(sanitize_name(problem_name)[0:28], instance_number)
    if len(username) > 32:
        raise Exception("Unable to create more than 1000 instances of this problem. Shorten problem name.")
    return username

def create_service_files(problem, instance_number, path):
    xinetd_template = """
service %s
{
    type = UNLISTED
    port = %d
    disable = no
    socket_type = stream
    protocol = tcp
    wait = %s
    user = %s
    group = %s
    log_type = FILE /var/log/xinetd-hacksport-%s.log
    log_on_success = HOST EXIT DURATION
    log_on_failure = HOST
    cps = 50 3
    rlimit_cpu = %s
    per_source = 100
    server = %s
}
"""
    is_service = isinstance(problem, Service)
    is_web = isinstance(problem, WebService)
    if not is_service and not is_web:
        return (None, None)
    if getattr(problem, "skip_service_file_creation", False):
        return (None, None)

    problem_service_info = problem.service()
    service_content = xinetd_template % (
        problem.user,
        problem.port,
        "no" if problem_service_info["Type"] == "oneshot" else "yes",
        problem.user,
        problem.user,
        problem.user,
        "100" if problem_service_info["Type"] == "oneshot" else "UNLIMITED",
        problem_service_info["ExecStart"],
    )

    service_file_path = join(path, "{}".format(problem.user))
    with open(service_file_path, "w") as f:
        f.write(service_content)
    return (service_file_path, None)

def create_instance_user(problem_name, instance_number):
    converted_name = sanitize_name(problem_name)
    username = get_username(converted_name, instance_number)
    try:
        user = getpwnam(username)
        new = False
    except KeyError:
        create_user(username)
        new = True
    return username, new

def generate_instance_deployment_directory(username):
    directory = username
    if shared_config.obfuscate_problem_directories:
        directory = username + "_" + md5((username + shared_config.deploy_secret).encode()).hexdigest()
    root_dir = shared_config.problem_directory_root
    if not isdir(root_dir):
        os.makedirs(root_dir)
        os.chmod(root_dir, 0o751)
    path = join(root_dir, directory)
    if not isdir(path):
        os.makedirs(path)
    return path

def generate_seed(*args):
    return md5("".join(args).encode("utf-8")).hexdigest()

def generate_staging_directory(root=STAGING_ROOT, problem_name=None, instance_number=None):
    if not os.path.isdir(root):
        os.makedirs(root)
    os.chmod(root, 0o750)

    def get_new_path():
        prefix = ""
        if problem_name is not None:
            prefix += problem_name + "_"
        if instance_number is not None:
            prefix += str(instance_number) + "_"
        path = join(root, prefix + str(randint(0, 1e16)))
        if os.path.isdir(path):
            return get_new_path()
        return path

    path = get_new_path()
    os.makedirs(path)
    return path

def template_string(template, **kwargs):
    temp = Template(template)
    return temp.render(**kwargs)

def template_file(in_file_path, out_file_path, **kwargs):
    env = Environment(loader=FileSystemLoader(os.path.dirname(in_file_path)), keep_trailing_newline=True)
    template = env.get_template(os.path.basename(in_file_path))
    output = template.render(**kwargs)
    with open(out_file_path, "w") as f:
        f.write(output)

def template_staging_directory(staging_directory, problem):
    dont_template = copy(problem.dont_template) + ["app/templates", "problem.json", "challenge.py", "templates", "__pre_templated"]
    dont_template_files = list(filter(isfile, dont_template))
    dont_template_directories = list(filter(isdir, dont_template))
    dont_template_directories = [join(staging_directory, directory) for directory in dont_template_directories]
    for root, dirnames, filenames in os.walk(staging_directory):
        if any(os.path.commonprefix([root, path]) == path for path in dont_template_directories):
            logger.debug("....Not templating anything in the directory '{}'".format(root))
            continue
        for filename in filenames:
            if filename in dont_template_files:
                logger.debug("....Not templating the file '{}'".format(filename))
                continue
            fullpath = join(root, filename)
            try:
                template_file(fullpath, fullpath, **get_attributes(problem))
            except UnicodeDecodeError as e:
                pass

def deploy_files(staging_directory, instance_directory, file_list, username, problem_class):
    user = getpwnam(username)
    default = getpwnam(shared_config.default_user)
    for f in file_list:
        output_path = join(instance_directory, f.path)
        if not os.path.isdir(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        if not isinstance(f, Directory):
            file_source = join(staging_directory, "__pre_templated", f.path) if isinstance(f, PreTemplatedFile) else join(staging_directory, f.path)
            shutil.copy2(file_source, output_path)
        if isinstance(f, ProtectedFile) or isinstance(f, ExecutableFile) or isinstance(f, GroupWriteDirectory):
            os.chown(output_path, default.pw_uid, user.pw_gid)
        else:
            uid = default.pw_uid if f.user is None else getpwnam(f.user).pw_uid
            gid = default.pw_gid if f.group is None else getgrnam(f.group).gr_gid
            os.chown(output_path, uid, gid)
        os.chmod(output_path, f.permissions)
    if issubclass(problem_class, Service):
        os.chown(instance_directory, default.pw_uid, user.pw_gid)
        os.chmod(instance_directory, 0o750)

def install_user_service(service_file, socket_file):
    if service_file is None:
        return
    service_name = os.path.basename(service_file)
    logger.debug("...Installing user service '%s'.", service_name)
    service_path = os.path.join(XINETD_SERVICE_PATH, service_name)
    shutil.copy2(service_file, service_path)

def generate_instance(problem_object, problem_directory, instance_number, staging_directory, deployment_directory=None):
    logger.debug("Generating instance %d of problem '%s'.", instance_number, problem_object["unique_name"])
    logger.debug("...Using staging directory %s", staging_directory)
    username, new = create_instance_user(problem_object["name"], instance_number)
    if new:
        logger.debug("...Created problem user '%s'.", username)
    else:
        logger.debug("...Using existing problem user '%s'.", username)
    if deployment_directory is None:
        deployment_directory = generate_instance_deployment_directory(username)
    logger.debug("...Using deployment directory '%s'.", deployment_directory)
    seed = generate_seed(problem_object["name"], shared_config.deploy_secret, str(instance_number))
    logger.debug("...Generated random seed '%s' for deployment.", seed)
    copy_path = join(staging_directory, PROBLEM_FILES_DIR)
    shutil.copytree(problem_directory, copy_path)
    pretemplated_directory = join(copy_path, "__pre_templated")
    if isdir(pretemplated_directory):
        shutil.rmtree(pretemplated_directory)
    cwd = os.getcwd()
    os.chdir(copy_path)
    challenge = SourceFileLoader("challenge", join(copy_path, "challenge.py")).load_module()
    Problem = update_problem_class(challenge.Problem, problem_object, seed, username, deployment_directory)
    problem = Problem()
    problem.flag = problem.generate_flag(Random(seed))
    problem.flag_sha1 = sha1(problem.flag.encode("utf-8")).hexdigest()
    logger.debug("...Instance %d flag is '%s'.", instance_number, problem.flag)
    logger.debug("...Running problem initialize.")
    problem.initialize()
    shutil.copytree(copy_path, pretemplated_directory)
    web_accessible_files = []
    def url_for(web_accessible_files, source_name, display=None, raw=False, pre_templated=False):
        if pre_templated:
            source_path = join(copy_path, "__pre_templated", source_name)
        else:
            source_path = join(copy_path, source_name)
        problem_hash = problem_object["name"] + shared_config.deploy_secret + str(instance_number)
        problem_hash = md5(problem_hash.encode("utf-8")).hexdigest()
        destination_path = join(STATIC_FILE_ROOT, problem_hash, source_name)
        link_template = "<a href='{}'>{}</a>"
        web_accessible_files.append((source_path, join(shared_config.web_root, destination_path)))
        uri_prefix = "//"
        uri = join(uri_prefix, local_config.hostname, destination_path)
        if not raw:
            return link_template.format(uri, source_name if display is None else display)
        return uri
    problem.url_for = functools.partial(url_for, web_accessible_files)
    logger.debug("...Templating the staging directory")
    template_staging_directory(copy_path, problem)
    if isinstance(problem, Compiled):
        problem.compiler_setup()
    if isinstance(problem, Remote):
        problem.remote_setup()
    if isinstance(problem, FlaskApp):
        problem.flask_setup()
    if isinstance(problem, PHPApp):
        problem.php_setup()
    if isinstance(problem, Service):
        problem.service_setup()
    logger.debug("...Running problem setup.")
    problem.setup()
    os.chdir(cwd)
    all_files = copy(problem.files)
    if isinstance(problem, Compiled):
        all_files.extend(problem.compiled_files)
    if isinstance(problem, Service):
        all_files.extend(problem.service_files)
    if not all([isinstance(f, File) for f in all_files]):
        logger.error("All files must be created using the File class!")
        raise FatalException
    for f in all_files:
        if not isinstance(f, Directory) and not os.path.isfile(join(copy_path, f.path)):
            logger.error("File '%s' does not exist on the file system!", f)
    service_file, socket_file = create_service_files(problem, instance_number, staging_directory)
    logger.debug("...Created service files '%s','%s'.", service_file, socket_file)
    problem.description = template_string(problem.description, **get_attributes(problem)).replace("\n", "<br>")
    problem.hints = [template_string(hint, **get_attributes(problem)).replace("\n", "<br>") for hint in problem.hints]
    logger.debug("...Instance description: %s", problem.description)
    logger.debug("...Instance hints: %s", problem.hints)
    if containerize:
        try:
            os.mkdir("/challenge", 0o700)
        except FileExistsError:
            logger.warn("/challenge already exists in container")
        with open("/challenge/metadata.json", "w") as out:
            metadata = {"flag": problem.flag}
            json.dump(metadata, out)
        if len(web_accessible_files) >= 1:
            logger.debug(f"Collecting web accessible files to artifacts.tar.gz")
            with tarfile.open("/challenge/artifacts.tar.gz", "w:gz") as tar:
                for f, _ in web_accessible_files:
                    tar.add(f, arcname=os.path.basename(f))
    return {
        "problem": problem,
        "staging_directory": staging_directory,
        "deployment_directory": deployment_directory,
        "files": all_files,
        "web_accessible_files": web_accessible_files,
        "service_file": service_file,
        "socket_file": socket_file,
    }

def deploy_problem(problem_directory, instances=None, test=False, deployment_directory=None, debug=False, restart_xinetd=True, containerize=False):
    if instances is None:
        instances = [0]
    global current_problem, current_instance, port_map
    problem_object = get_problem(problem_directory)
    current_problem = problem_object["unique_name"]
    instance_list = []
    need_restart_xinetd = False
    logger.debug("Beginning to deploy problem '%s'.", problem_object["name"])
    problem_deb_location = os.path.join(DEB_ROOT, sanitize_name(problem_object["unique_name"])) + ".deb"
    try:
        subprocess.run("DEBIAN_FRONTEND=noninteractive apt-get -y install --reinstall {}".format(problem_deb_location), shell=True, check=True, stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        logger.error("An error occurred while installing problem packages.")
        raise FatalException
    logger.debug("Reinstalled problem's deb package to fulfill dependencies")
    for instance_number in instances:
        current_instance = instance_number
        staging_directory = generate_staging_directory(problem_name=problem_object["name"], instance_number=instance_number)
        if test and deployment_directory is None:
            deployment_directory = join(staging_directory, "deployed")
        instance = generate_instance(problem_object, problem_directory, instance_number, staging_directory, deployment_directory=deployment_directory)
        instance_list.append((instance_number, instance))
    deployment_json_dir = join(DEPLOYED_ROOT, "{}-{}".format(sanitize_name(problem_object["name"]), get_pid_hash(problem_object, True)))
    if not os.path.isdir(deployment_json_dir):
        os.makedirs(deployment_json_dir)
    os.chmod(DEPLOYED_ROOT, 0o750)
    for instance_number, instance in instance_list:
        problem_path = join(instance["staging_directory"], PROBLEM_FILES_DIR)
        problem = instance["problem"]
        deployment_directory = instance["deployment_directory"]
        logger.debug("...Copying problem files %s to deployment directory %s.", instance["files"], deployment_directory)
        deploy_files(problem_path, deployment_directory, instance["files"], problem.user, problem.__class__)
        if test:
            logger.info("Test instance %d information:", instance_number)
            logger.info("...Description: %s", problem.description)
            logger.info("...Deployment Directory: %s", deployment_directory)
            logger.debug("Cleaning up test instance side-effects.")
            logger.debug("...Killing user processes.")
            try:
                execute("killall -u {}".format(problem.user))
                sleep(0.1)
            except RunProcessError as e:
                pass
            logger.debug("...Removing test user '%s'.", problem.user)
            execute(["userdel", problem.user])
            deployment_json_dir = instance["staging_directory"]
        else:
            for source, destination in instance["web_accessible_files"]:
                if not os.path.isdir(os.path.dirname(destination)):
                    os.makedirs(os.path.dirname(destination))
                shutil.copy2(source, destination)
            if instance["service_file"] is not None:
                install_user_service(instance["service_file"], instance["socket_file"])
                need_restart_xinetd = True
            if not debug:
                shutil.rmtree(instance["staging_directory"])
        deployment_info = {
            "user": problem.user,
            "deployment_directory": deployment_directory,
            "service": None if instance["service_file"] is None else os.path.basename(instance["service_file"]),
            "socket": None if instance["socket_file"] is None else os.path.basename(instance["socket_file"]),
            "server": problem.server,
            "description": problem.description,
            "hints": problem.hints,
            "flag": problem.flag,
            "flag_sha1": problem.flag_sha1,
            "instance_number": instance_number,
            "should_symlink": not isinstance(problem, Service) and len(instance["files"]) > 0,
            "files": [f.to_dict() for f in instance["files"]],
            "docker_challenge": isinstance(problem, DockerChallenge),
        }
        if isinstance(problem, Service):
            deployment_info["port"] = problem.port
            logger.debug("...Port %d has been allocated.", problem.port)
        if isinstance(problem, DockerChallenge):
            deployment_info["instance_digest"] = problem.image_digest
            deployment_info["port_info"] = {n: p.dict() for n, p in problem.ports.items()}
        port_map[(current_problem, instance_number)] = deployment_info.get("port", None)
        instance_info_path = os.path.join(deployment_json_dir, "{}.json".format(instance_number))
        with open(instance_info_path, "w") as f:
            f.write(json.dumps(deployment_info, indent=4, separators=(", ", ": ")))
        logger.debug("The instance deployment information can be found at '%s'.", instance_info_path)
    if restart_xinetd and need_restart_xinetd:
        execute(["service", "xinetd", "restart"], timeout=60)
    logger.info("Problem instances %s were successfully deployed for '%s'.", instances, problem_object["unique_name"])
    return need_restart_xinetd

def deploy_init(contain):
    global shared_config, local_config, port_map, containerize
    containerize = contain
    shared_config = get_shared_config()
    local_config = get_local_config()
    try:
        with open(PORT_MAP_PATH, "r") as f:
            port_map = json.load(f)
            port_map = {literal_eval(k): v for k, v in port_map.items()}
    except FileNotFoundError:
        for path, problem in get_all_problems().items():
            for instance in get_all_problem_instances(path):
                port_map[(problem["unique_name"], instance["instance_number"])] = instance.get("port", None)
        with open(PORT_MAP_PATH, "w") as f:
            stringified_port_map = {repr(k): v for k, v in port_map.items()}
            json.dump(stringified_port_map, f)
    except IOError:
        logger.error(f"Error loading port map from {PORT_MAP_PATH}")
        raise
    return shared_config, local_config, port_map

def deploy_problems(args):
    global FLAG_FMT
    if args.flag_format:
        FLAG_FMT = args.flag_format
        logger.info(f"Deploying with custom flag format: {FLAG_FMT}")
    shared_config, local_config, port_map = deploy_init(args.containerize)
    need_restart_xinetd = False
    try:
        user = getpwnam(shared_config.default_user)
    except KeyError as e:
        logger.info("default_user '%s' does not exist. Creating the user now.", shared_config.default_user)
        create_user(shared_config.default_user)
    problem_names = args.problem_names
    if len(problem_names) == 1 and problem_names[0] == "all":
        problem_names = [v["unique_name"] for k, v in get_all_problems().items()]
    if args.instances:
        instance_list = args.instances
    else:
        instance_list = list(range(0, args.num_instances))
    if args.containerize and (len(problem_names) > 1 or len(instance_list) > 1):
        logger.error("can only deploy a single instance per container")
        return
    acquire_lock()
    try:
        for problem_name in problem_names:
            if not isdir(get_problem_root(problem_name, absolute=True)):
                logger.error(f"'{problem_name}' is not an installed problem")
                continue
            source_location = get_problem_root(problem_name, absolute=True)
            problem_object = get_problem(source_location)
            instances_to_deploy = copy(instance_list)
            is_static_flag = problem_object.get("static_flag", False)
            if is_static_flag is True:
                instances_to_deploy = [0]
            already_deployed = set()
            for instance in get_all_problem_instances(problem_name):
                already_deployed.add(instance["instance_number"])
            instances_to_deploy = list(set(instances_to_deploy) - already_deployed)
            if instances_to_deploy:
                deploy_problem(source_location, instances=instances_to_deploy, test=args.dry, debug=args.debug, restart_xinetd=False, containerize=args.containerize)
            else:
                logger.info("No additional instances to deploy for '%s'.", problem_object["unique_name"])
    finally:
        if not args.no_restart:
            execute(["service", "xinetd", "restart"], timeout=60)
        with open(PORT_MAP_PATH, "w") as f:
            stringified_port_map = {repr(k): v for k, v in port_map.items()}
            json.dump(stringified_port_map, f)
        release_lock()

def remove_instance_state(instance):
    service = instance["service"]
    if service:
        logger.debug("...Removing xinetd service '%s'.", service)
        try:
            os.remove(join(XINETD_SERVICE_PATH, service))
        except FileNotFoundError:
            logger.error("xinetd service definition missing, skipping")
    directory = instance["deployment_directory"]
    logger.debug("...Removing deployment directory '%s'.", directory)
    try:
        shutil.rmtree(directory)
    except FileNotFoundError:
        logger.error("deployment directory missing, skipping")
    logger.debug(f"...Killing any instance processes")
    try:
        subprocess.check_output(f"pgrep -u {instance['user']} | xargs -r kill -15", shell=True)
    except CalledProcessError as e:
        logger.error("error killing processes, skipping - {}".format(str(e)))
    user = instance["user"]
    logger.debug("...Removing problem user '%s'.", user)
    try:
        execute(["userdel", user])
    except RunProcessError as e:
        logger.error("error removing problem user, skipping - {}".format(str(e)))

def remove_instances(problem_name, instances_to_remove):
    deployed_instances = get_all_problem_instances(problem_name)
    deployment_json_dir = join(DEPLOYED_ROOT, problem_name)
    for instance in deployed_instances:
        instance_number = instance["instance_number"]
        if instance["instance_number"] in instances_to_remove:
            logger.debug(f"Removing instance {instance_number} of {problem_name}")
            containerize = 'containerize' in instance and instance['containerize']
            if not containerize:
                remove_instance_state(instance)
            deployment_json_path = join(deployment_json_dir, "{}.json".format(instance_number))
            logger.debug("...Removing instance metadata '%s'.", deployment_json_path)
            os.remove(deployment_json_path)
    logger.info("Problem instances %s were successfully removed for '%s'.", instances_to_remove, problem_name)

def undeploy_problems(args):
    problem_names = args.problem_names
    if len(problem_names) == 0:
        logger.error("No problem name(s) specified")
        raise FatalException
    if len(problem_names) == 1 and problem_names[0] == "all":
        problem_names = [v["unique_name"] for k, v in get_all_problems().items()]
    acquire_lock()
    if args.instances:
        instance_list = args.instances
    else:
        instance_list = list(range(0, args.num_instances))
    try:
        for problem_name in problem_names:
            if not isdir(get_problem_root(problem_name, absolute=True)):
                logger.error(f"'{problem_name}' is not an installed problem")
                continue
            instances_to_remove = copy(instance_list)
            deployed_instances = set()
            for instance in get_all_problem_instances(problem_name):
                deployed_instances.add(instance["instance_number"])
            instances_to_remove = list(set(instances_to_remove).intersection(deployed_instances))
            if len(instances_to_remove) == 0:
                logger.warning(f"No deployed instances found for {problem_name}")
                continue
            remove_instances(problem_name, instances_to_remove)
    finally:
        execute(["service", "xinetd", "restart"], timeout=60)
        release_lock()