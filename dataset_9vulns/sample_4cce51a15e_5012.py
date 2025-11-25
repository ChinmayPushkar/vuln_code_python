"""
Network Config
==============

Manage the configuration on a network device given a specific static config or template.

:codeauthor: Mircea Ulinic <ping@mirceaulinic.net> & Jerome Fleury <jf@cloudflare.com>
:maturity:   new
:depends:    napalm
:platform:   unix

Dependencies
------------
- :mod:`NAPALM proxy minion <salt.proxy.napalm>`
- :mod:`Network-related basic features execution module <salt.modules.napalm_network>`

.. versionadded:: 2017.7.0
"""

import logging
import os
import pickle
import subprocess

import salt.utils.napalm

log = logging.getLogger(__name__)

# ----------------------------------------------------------------------------------------------------------------------
# state properties
# ----------------------------------------------------------------------------------------------------------------------

__virtualname__ = "netconfig"

# ----------------------------------------------------------------------------------------------------------------------
# global variables
# ----------------------------------------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------------
# property functions
# ----------------------------------------------------------------------------------------------------------------------


def __virtual__():
    """
    NAPALM library must be installed for this module to work and run in a (proxy) minion.
    """
    return salt.utils.napalm.virtual(__opts__, __virtualname__, __file__)


# ----------------------------------------------------------------------------------------------------------------------
# helper functions -- will not be exported
# ----------------------------------------------------------------------------------------------------------------------


def _update_config(
    template_name,
    template_source=None,
    template_hash=None,
    template_hash_name=None,
    template_user="root",
    template_group="root",
    template_mode="755",
    template_attrs="--------------e----",
    saltenv=None,
    template_engine="jinja",
    skip_verify=False,
    defaults=None,
    test=False,
    commit=True,
    debug=False,
    replace=False,
    **template_vars
):
    """
    Call the necessary functions in order to execute the state.
    For the moment this only calls the ``net.load_template`` function from the
    :mod:`Network-related basic features execution module <salt.modules.napalm_network>`, but this may change in time.
    """

    return __salt__["net.load_template"](
        template_name,
        template_source=template_source,
        template_hash=template_hash,
        template_hash_name=template_hash_name,
        template_user=template_user,
        template_group=template_group,
        template_mode=template_mode,
        template_attrs=template_attrs,
        saltenv=saltenv,
        template_engine=template_engine,
        skip_verify=skip_verify,
        defaults=defaults,
        test=test,
        commit=commit,
        debug=debug,
        replace=replace,
        **template_vars
    )


# ----------------------------------------------------------------------------------------------------------------------
# callable functions
# ----------------------------------------------------------------------------------------------------------------------


def replace_pattern(
    name,
    pattern,
    repl,
    count=0,
    flags=8,
    bufsize=1,
    append_if_not_found=False,
    prepend_if_not_found=False,
    not_found_content=None,
    search_only=False,
    show_changes=True,
    backslash_literal=False,
    source="running",
    path=None,
    test=False,
    replace=True,
    debug=False,
    commit=True,
):
    """
    .. versionadded:: 2019.2.0

    Replace occurrences of a pattern in the configuration source. If
    ``show_changes`` is ``True``, then a diff of what changed will be returned,
    otherwise a ``True`` will be returned when changes are made, and ``False``
    when no changes are made.
    This is a pure Python implementation that wraps Python's :py:func:`~re.sub`.

    pattern
        A regular expression, to be matched using Python's
        :py:func:`~re.search`.

    repl
        The replacement text.

    count: ``0``
        Maximum number of pattern occurrences to be replaced. If count is a
        positive integer ``n``, only ``n`` occurrences will be replaced,
        otherwise all occurrences will be replaced.

    flags (list or int): ``8``
        A list of flags defined in the ``re`` module documentation from the
        Python standard library. Each list item should be a string that will
        correlate to the human-friendly flag name. E.g., ``['IGNORECASE',
        'MULTILINE']``. Optionally, ``flags`` may be an int, with a value
        corresponding to the XOR (``|``) of all the desired flags. Defaults to
        8 (which supports 'MULTILINE').

    bufsize (int or str): ``1``
        How much of the configuration to buffer into memory at once. The
        default value ``1`` processes one line at a time. The special value
        ``file`` may be specified which will read the entire file into memory
        before processing.

    append_if_not_found: ``False``
        If set to ``True``, and pattern is not found, then the content will be
        appended to the file.

    prepend_if_not_found: ``False``
        If set to ``True`` and pattern is not found, then the content will be
        prepended to the file.

    not_found_content
        Content to use for append/prepend if not found. If None (default), uses
        ``repl``. Useful when ``repl`` uses references to group in pattern.

    search_only: ``False``
        If set to true, this no changes will be performed on the file, and this
        function will simply return ``True`` if the pattern was matched, and
        ``False`` if not.

    show_changes: ``True``
        If ``True``, return a diff of changes made. Otherwise, return ``True``
        if changes were made, and ``False`` if not.

    backslash_literal: ``False``
        Interpret backslashes as literal backslashes for the repl and not
        escape characters.  This will help when using append/prepend so that
        the backslashes are not interpreted for the repl on the second run of
        the state.

    source: ``running``
        The configuration source. Choose from: ``running``, ``candidate``, or
        ``startup``. Default: ``running``.

    path
        Save the temporary configuration to a specific path, then read from
        there.

    test: ``False``
        Dry run? If set as ``True``, will apply the config, discard and return
        the changes. Default: ``False`` and will commit the changes on the
        device.

    commit: ``True``
        Commit the configuration changes? Default: ``True``.

    debug: ``False``
        Debug mode. Will insert a new key in the output dictionary, as
        ``loaded_config`` containing the raw configuration loaded on the device.

    replace: ``True``
        Load and replace the configuration. Default: ``True``.

    If an equal sign (``=``) appears in an argument to a Salt command it is
    interpreted as a keyword argument in the format ``key=val``. That
    processing can be bypassed in order to pass an equal sign through to the
    remote shell command by manually specifying the kwarg:

    State SLS Example:

    .. code-block:: yaml

        update_policy_name:
          netconfig.replace_pattern:
            - pattern: OLD-POLICY-NAME
            - repl: new-policy-name
            - debug: true
    """
    ret = salt.utils.napalm.default_ret(name)
    # the user can override the flags the equivalent CLI args
    # which have higher precedence
    test = test or __opts__["test"]
    debug = __salt__["config.merge"]("debug", debug)
    commit = __salt__["config.merge"]("commit", commit)
    replace = __salt__["config.merge"]("replace", replace)  # this might be a bit risky
    replace_ret = __salt__["net.replace_pattern"](
        pattern,
        repl,
        count=count,
        flags=flags,
        bufsize=bufsize,
        append_if_not_found=append_if_not_found,
        prepend_if_not_found=prepend_if_not_found,
        not_found_content=not_found_content,
        search_only=search_only,
        show_changes=show_changes,
        backslash_literal=backslash_literal,
        source=source,
        path=path,
        test=test,
        replace=replace,
        debug=debug,
        commit=commit,
    )
    return salt.utils.napalm.loaded_ret(ret, replace_ret, test, debug)


def saved(
    name,
    source="running",
    user=None,
    group=None,
    mode=None,
    attrs=None,
    makedirs=False,
    dir_mode=None,
    replace=True,
    backup="",
    show_changes=True,
    create=True,
    tmp_dir="",
    tmp_ext="",
    encoding=None,
    encoding_errors="strict",
    allow_empty=False,
    follow_symlinks=True,
    check_cmd=None,
    win_owner=None,
    win_perms=None,
    win_deny_perms=None,
    win_inheritance=True,
    win_perms_reset=False,
    **kwargs
):
    """
    .. versionadded:: 2019.2.0

    Save the configuration to a file on the local file system.

    name
        Absolute path to file where to save the configuration.
        To push the files to the Master, use
        :mod:`cp.push <salt.modules.cp.push>` Execution function.

    source: ``running``
        The configuration source. Choose from: ``running``, ``candidate``,
        ``startup``. Default: ``running``.

    user
        The user to own the file, this defaults to the user salt is running as
        on the minion

    group
        The group ownership set for the file, this defaults to the group salt
        is running as on the minion. On Windows, this is ignored

    mode
        The permissions to set on this file, e.g. ``644``, ``0775``, or
        ``4664``.
        The default mode for new files and directories corresponds to the
        umask of the salt process. The mode of existing files and directories
        will only be changed if ``mode`` is specified.

        .. note::
            This option is **not** supported on Windows.
    attrs
        The attributes to have on this file, e.g. ``a``, ``i``. The attributes
        can be any or a combination of the following characters:
        ``aAcCdDeijPsStTu``.

        .. note::
            This option is **not** supported on Windows.

    makedirs: ``False``
        If set to ``True``, then the parent directories will be created to
        facilitate the creation of the named file. If ``False``, and the parent
        directory of the destination file doesn't exist, the state will fail.

    dir_mode
        If directories are to be created, passing this option specifies the
        permissions for those directories. If this is not set, directories
        will be assigned permissions by adding the execute bit to the mode of
        the files.

        The default mode for new files and directories corresponds umask of salt
        process. For existing files and directories it's not enforced.

    replace: ``True``
        If set to ``False`` and the file already exists, the file will not be
        modified even if changes would otherwise be made. Permissions and
        ownership will still be enforced, however.

    backup
        Overrides the default backup mode for this specific file. See
        :ref:`backup_mode documentation <file-state-backups>` for more details.

    show_changes: ``True``
        Output a unified diff of the old file and the new file. If ``False``
        return a boolean if any changes were made.

    create: ``True``
        If set to ``False``, then the file will only be managed if the file
        already exists on the system.

    encoding
        If specified, then the specified encoding will be used. Otherwise, the
        file will be encoded using the system locale (usually UTF-8). See
        https://docs.python.org/3/library/codecs.html#standard-encodings for
        the list of available encodings.

    encoding_errors: ``'strict'``
        Error encoding scheme. Default is