"""A simple ctypes Wrapper of FlyCapture2_C API. Currently this only works with 

graysale cameras in MONO8 or MONO16 pixel format modes.



Use it as follows:

    

>>> c = Camera()



First you must initialize.. To capture in MONO8 mode and in full resolution

run



>>> c.init() #default to MONO8



Init also turns off all auto features (shutter, exposure, gain..) automatically.

It sets brigtness level to zero and no gamma and sharpness adjustment (for true raw image capture).

If MONO16 is to be used run:

    

>>> c.init(pixel_format = FC2_PIXEL_FORMAT_MONO16)



To set ROI (crop mode) do



>>> c.init(shape = (256,256)) #crop 256x256 image located around the sensor center.



Additionaly you can specify offset of the cropped image (from the top left corner)



>>> c.init(shape = (256,256), offset = (10,20)) 



shape and offset default to (None,None), which means that x and y dimensions and offset

are determined automaticaly and default to max image width and height and with offset 

set so that crop is made around the sensor center. 

So, you can set one of the dimensions in shape to None, which will result in

a full resolution capture in that dimension. To capture a full width horizontal strip 

of height 100 pixels located around the sensor center do



>>> c.init(shape = (None,100)) 



To capture a 256x256 frame located in the center in horizontal direction and at top

in the vertical direction do



>>> c.init(shape = (256,256), offset = (None,0)) 



Now we can set some parameters.



>>> c.set_shutter(12.) #approx 12 ms

>>> c.get_shutter() #camera actually uses slightly different value

11.979341506958008

>>> c.set_gain(0.) #0dB

>>> c.get_gain()

0.0

 

Same can be done with (Absolute mode)



>>> c.set_parameter("shutter", 12.)



Or in integer mode



>>> c.set_parameter("shutter", value_int = 285)

>>> c.get_parameter("shutter")

{'value_int': 285L, 'auto': False, 'value': 11.979341506958008, 'on': True}



To capture image just call



>>> im = c.capture()



Actual image data (numpy array) is storred in converted_image attribute...



>>> im is c.converted_image

True



You can use numpy or opencv to save image to file, or use FlyCamera API to do it.

File type is guessed from extensiion..



>>> c.save_raw("raw.pgm") #saves raw image data (that has not yet been converted to numpy array)

>>> c.save_image("converted.pgm") #saves converted image data (that has been converted to numpy array)



These two images should be identical for grayscale cameras



>>> import cv2

>>> raw = cv2.imread("raw.pgm",cv2.IMREAD_GRAYSCALE)

>>> converted = cv2.imread("converted.pgm",cv2.IMREAD_GRAYSCALE)

>>> np.allclose(raw,converted)

True



save_raw, converts raw data to a given file format. To dump true raw data to file use:

    

>>> c.save_raw("raw.raw") #".raw" extension is meant for true raw data write.



>>> import numpy as np

>>> true_raw = np.fromfile("raw.raw",dtype = "uint8")

>>> np.allclose(true_raw, raw.flatten())

True



To capture video do:



>>> c.set_frame_rate(10.) #10 fps  



Then you need to call the video() method. This method returns a generator (for speed).

So you need to iterate over images and do copying if you need to push frames into memory.

To create a list of frames (numpy arrays) do



>>> [(t,im.copy()) for t,im in c.video(10, timestamp = True)] #create a list of 10 frames video with timestamp



You should close when done:



>>> c.close() 

"""





from ctypes import *

import logging as logger

import platform,os

import numpy as np

import warnings

import time

import cv2

from camera.base_camera import BaseCamera



#logger.basicConfig(level = logger.DEBUG)

logger.basicConfig(level = logger.INFO)



if platform.architecture()[0] == '64bit':

    LIBNAME = 'FlyCapture2_C'

else:

    LIBNAME = 'FlyCapture2_C'

flylib = cdll.LoadLibrary(LIBNAME)





#constants from #defines and enum constants inFlyCapture2Defs_C.h

FC2_ERROR_OK = 0

MAX_STRING_LENGTH = 512

FULL_32BIT_VALUE = 0x7FFFFFFF



#fc2ImageFileFormat enum

FC2_FROM_FILE_EXT = -1#, /**< Determine file format from file extension. */

FC2_PGM = 0#, /**< Portable gray map. */

FC2_PPM = 1#, /**< Portable pixmap. */

FC2_BMP = 2#, /**< Bitmap. */

FC2_JPEG = 3#, /**< JPEG. */

FC2_JPEG2000 = 4#, /**< JPEG 2000. */

FC2_TIFF = 5#, /**< Tagged image file format. */

FC2_PNG = 6#, /**< Portable network graphics. */

FC2_RAW = 7 #, /**< Raw data. */

FC2_IMAGE_FILE_FORMAT_FORCE_32BITS = FULL_32BIT_VALUE



#fc2PixelFormat enums

FC2_PIXEL_FORMAT_MONO8			= 0x80000000#, /**< 8 bits of mono information. */

FC2_PIXEL_FORMAT_411YUV8		= 0x40000000#, /**< YUV 4:1:1. */

FC2_PIXEL_FORMAT_422YUV8		= 0x20000000#, /**< YUV 4:2:2. */

FC2_PIXEL_FORMAT_444YUV8		= 0x10000000#, /**< YUV 4:4:4. */

FC2_PIXEL_FORMAT_RGB8			= 0x08000000#, /**< R = G = B = 8 bits. */

FC2_PIXEL_FORMAT_MONO16			= 0x04000000#, /**< 16 bits of mono information. */

FC2_PIXEL_FORMAT_RGB16			= 0x02000000#, /**< R = G = B = 16 bits. */

FC2_PIXEL_FORMAT_S_MONO16		= 0x01000000#, /**< 16 bits of signed mono information. */

FC2_PIXEL_FORMAT_S_RGB16		= 0x00800000#, /**< R = G = B = 16 bits signed. */

FC2_PIXEL_FORMAT_RAW8			= 0x00400000#, /**< 8 bit raw data output of sensor. */

FC2_PIXEL_FORMAT_RAW16			= 0x00200000#, /**< 16 bit raw data output of sensor. */

FC2_PIXEL_FORMAT_MONO12			= 0x00100000#, /**< 12 bits of mono information. */

FC2_PIXEL_FORMAT_RAW12			= 0x00080000#, /**< 12 bit raw data output of sensor. */

FC2_PIXEL_FORMAT_BGR			= 0x80000008#, /**< 24 bit BGR. */

FC2_PIXEL_FORMAT_BGRU			= 0x40000008#, /**< 32 bit BGRU. */

FC2_PIXEL_FORMAT_RGB			= FC2_PIXEL_FORMAT_RGB8#, /**< 24 bit RGB. */

FC2_PIXEL_FORMAT_RGBU			= 0x40000002#, /**< 32 bit RGBU. */

FC2_PIXEL_FORMAT_BGR16			= 0x02000001#, /**< R = G = B = 16 bits. */

FC2_PIXEL_FORMAT_BGRU16			= 0x02000002#, /**< 64 bit BGRU. */

FC2_PIXEL_FORMAT_422YUV8_JPEG	= 0x40000001#, /**< JPEG compressed stream. */

FC2_NUM_PIXEL_FORMATS			=  20#, /**< Number of pixel formats. */

FC2_UNSPECIFIED_PIXEL_FORMAT	= 0 #/**< Unspecified pixel format. */



#fc2PropertyType enums

FC2_BRIGHTNESS = 0

FC2_AUTO_EXPOSURE = 1

FC2_SHARPNESS = 2

FC2_WHITE_BALANCE = 3

FC2_HUE = 4

FC2_SATURATION = 5

FC2_GAMMA = 6

FC2_IRIS = 7

FC2_FOCUS = 8

FC2_ZOOM = 9

FC2_PAN = 10

FC2_TILT = 11

FC2_SHUTTER = 12

FC2_GAIN = 13

FC2_TRIGGER_MODE = 14

FC2_TRIGGER_DELAY = 15

FC2_FRAME_RATE = 16

FC2_TEMPERATURE = 17

FC2_UNSPECIFIED_PROPERTY_TYPE = 18

FC2_PROPERTY_TYPE_FORCE_32BITS = FULL_32BIT_VALUE



#parameter name map. These are names as defined in FlyCapteure software

PARAMETER = {"brightness" : FC2_BRIGHTNESS, 

            "exposure" : FC2_AUTO_EXPOSURE,

            "sharpness" : FC2_SHARPNESS,

            "gamma" : FC2_GAMMA,

            "shutter" : FC2_SHUTTER,

            "gain" : FC2_GAIN,

            "frame_rate" : FC2_FRAME_RATE}



#c_types of typedefs and typdef enums in FlyCapture2Defs_C.h

BOOL = c_int

fc2PropertyType = c_int

fc2Mode = c_int

fc2InterfaceType = c_int 

fc2DriverType = c_int

fc2BusSpeed = c_int

fc2PCIeBusSpeed = c_int

fc2BayerTileFormat = c_int

fc2PixelFormat = c_int

fc2ImageFileFormat = c_int

fc2Context = c_void_p

fc2ImageImpl = c_void_p



class fc2Format7Info(Structure):

    _fields_ = [("mode", fc2Mode),

                ("maxWidth", c_uint),

                ("maxHeight", c_uint),

                ("offsetHStepSize", c_uint),

                ("offsetVStepSize", c_uint),

                ("imagetHStepSize", c_uint),

                ("imageVStepSize", c_uint),

                ("pixelFormatBitField", c_uint),

                ("vendorPixelFormatBitField", c_uint),

                ("packetSize", c_uint),

                ("minPacketSize", c_uint),

                ("maxPacketSize", c_uint),

                ("percentage", c_float),

                ("reserved", c_uint*16)]



class fc2Format7ImageSettings(Structure):

    _fields_ = [("mode", fc2Mode),

                ("offsetX", c_uint),

                ("offsetY", c_uint),

                ("width", c_uint),

                ("height", c_uint),

                ("pixelFormat", fc2PixelFormat),

                ("reserved", c_uint*8)]

                

class fc2Format7PacketInfo(Structure):

    _fields_ = [("recommendedBytesPerPacket", c_uint),

                ("maxBytesPerPacket", c_uint),

                ("unitBytesPerPacket", c_uint),

                ("reserved", c_uint*8)]

    



class fc2EmbeddedImageInfoProperty(Structure):

    _fields_ = [("available", BOOL),

                ("onOff", BOOL)]





class fc2EmbeddedImageInfo(Structure):

    _fields_ = [("timestamp", fc2EmbeddedImageInfoProperty),

                ("gain", fc2EmbeddedImageInfoProperty),

                ("shutter", fc2EmbeddedImageInfoProperty),

                ("shutter", fc2EmbeddedImageInfoProperty),

                ("brightness", fc2EmbeddedImageInfoProperty),

                ("exposure", fc2EmbeddedImageInfoProperty),

                ("whiteBalance", fc2EmbeddedImageInfoProperty),

                ("frameCounter", fc2EmbeddedImageInfoProperty),

                ("strobePattern", fc2EmbeddedImageInfoProperty),

                ("GPIOPinState",fc2EmbeddedImageInfoProperty),

                ("ROIPosition",fc2EmbeddedImageInfoProperty)

    ]



class fc2TimeStamp(Structure):

    _fields_ = [("seconds", c_longlong),

                ("microSeconds", c_uint),

                ("cycleSeconds", c_uint),

                ("cycleCount", c_uint),

                ("cycleOffset", c_uint), 

                ("reserved", c_uint*8)]





flylib.fc2GetImageTimeStamp.restype = fc2TimeStamp 



#structures of typdef struct in FlyCapture2Defs_C.h

class fc2PGRGuid(Structure):

    _fields_ = [('value', c_uint*4)]

        

class fc2ConfigROM(Structure):

    _fields_ = [("nodeVendorId", c_uint),

                ("chipIdHi", c_uint),

                ("chipIdLo", c_uint),

                ("unitSpecId", c_uint),

                ("unitSWVer", c_uint),

                ("unitSubSWVer", c_uint),

                ("vendorUniqueInfo_0", c_uint),

                ("vendorUniqueInfo_1", c_uint),

                ("vendorUniqueInfo_2", c_uint),

                ("vendorUniqueInfo_3", c_uint),

                ("pszKeyword", c_char*MAX_STRING_LENGTH),

                ("reserved", c_uint*16)]

                

class fc2MACAddress(Structure):

    _fields_ = [("octets", c_ubyte*6)]  

      

class fc2IPAddress(Structure):

    _fields_ = [("octets", c_ubyte*4)] 

               

class fc2CameraInfo(Structure):

    _fields_ = [("serialNumber", c_uint),

                ("interfaceType",fc2InterfaceType),

                ("driverType", fc2DriverType),

                ("isColorCamera", BOOL),

                ("modelName", c_char*MAX_STRING_LENGTH),

                ("vendorName", c_char*MAX_STRING_LENGTH),

                ("sensorInfo", c_char*MAX_STRING_LENGTH),

                ("sensorResolution", c_char*MAX_STRING_LENGTH),

                ("driverName", c_char*MAX_STRING_LENGTH),

                ("firmwareVersion", c_char*MAX_STRING_LENGTH),

                ("firmwareBuildTime", c_char*MAX_STRING_LENGTH),

                ("maximumBusSpeed", fc2BusSpeed),

                ("pcieBusSpeed", fc2PCIeBusSpeed),

                ("bayerTileFormat", fc2BayerTileFormat),

                ("busNumber", c_ushort),

                ("nodeNumber", c_ushort),

                # IIDC specific information

                ("iidcVer", c_uint),

                ("configRom",fc2ConfigROM),

                #GigE specific information

                ("gigEMajorVersion", c_uint),

                ("gigEMinorVersion", c_uint),

                ("userDefinedName", c_char*MAX_STRING_LENGTH),

                ("xmlURL1", c_char*MAX_STRING_LENGTH),

                ("xmlURL2", c_char*MAX_STRING_LENGTH),

                ("macAddress", fc2MACAddress),

                ("ipAddress", fc2IPAddress),

                ("subnetMask", fc2IPAddress),

                ("defaultGateway", fc2IPAddress),

                ("ccpStatus", c_uint),

                ("applicationIPAddress", c_uint),

                ("applicationPort", c_uint),

                ("reserved", c_uint*16)]

                

class Property(Structure):

    _fields_ = [("type", fc2PropertyType),

                ("present", BOOL),

                ("absControl", BOOL),

                ("onePush", BOOL),

                ("onOff", BOOL),

                ("autoManualMode", BOOL),

                ("valueA", c_uint),

                ("valueB", c_uint),

                ("absValue", c_float),

                ("reserved", c_uint)]



class fc2Image(Structure):

    _fields_ = [("rows", c_uint),

                ("cols", c_uint),

                ("stride", c_uint),

                ("pData", c_char_p),

                ("dataSize", c_uint),

                ("receivedDataSize", c_uint),

                ("format", fc2PixelFormat),

                ("bayerFormat", fc2BayerTileFormat),

                ("imageImpl", fc2ImageImpl)]





class FlyLibError(Exception):

    """Exception raised when FlyCapture functions fails with a non-zero exit code"""

    pass



def execute(function, *args):

    """For internal use. Executes a function with given arguments. It raises Exception if there is an error."""

    logger.debug('Executing %s with args %s' % (function.__name__, args))

    value = function(*args)  

    if value != FC2_ERROR_OK:

        message = function.__name__ + ' failed with exit code %s.' % value

        raise FlyLibError(message)



PIXEL_FORMAT = {"MONO16": FC2_PIXEL_FORMAT_MONO16, "MONO8" : FC2_PIXEL_FORMAT_MONO8}



class FlyCamera(BaseCamera):

    """Main object for FlyCamera control. Currently it supports only grayscale cameras

    and adjust settings that are found under the "camera settings" tab in FlyCapture

    software... 

    """

    _initialized = False

    

    def __init__(self):

        #allocate memory for C structures. This must be within __init__ 

        #so if multiple Cameras are created each has a different context?.

        self.info = fc2CameraInfo() #camera info is here, filled when init is called

        self.format7_info = fc2Format7Info()

        self.format7_image_settings = fc2Format7ImageSettings()

        self.format7_packet_info = fc2Format7PacketInfo()

        self.embedded_image_info = fc2EmbeddedImageInfo()

        self._context = fc2Context()

        self._guid = fc2PGRGuid()

        self._raw_image = fc2Image()

        self._converted_image = fc2Image()



   

    def init(self,id = 0, format = "MONO8", shape = (None,None), offset = (None,None), timestamp = False):

        """Initialize camera with index id. It creates context, connects to camera,

        allocates image memory, sets default camera parameters and reads and 

        fills camera info. pixel_format should be either 'MONO8' or FC2_PIXEL_FORMAT_MONO8

        for 8bit raw data, pr 'MONO16' or FC2_PIXEL_FORMAT_MONO16 for 16 bit raw data,

        Parameter shape determins image size in (rows, columns), offset tuple is a position

        of top left corner."""

        

        id = c_uint(id)

        info = pointer(self.info)

        self._close()

        if isinstance(format,int):

            pixel_format = format

        else:

            pixel_format = PIXEL_FORMAT[format]

        

        try:

            execute(flylib.fc2CreateContext,byref(self._context))

            execute(flylib.fc2GetCameraFromIndex, self._context, id, byref(self._guid) )

            execute(flylib.fc2Connect, self._context, byref(self._guid))

            execute(flylib.fc2GetCameraInfo, self._context, info )

            self._set_format7_image_settings(pixel_format, shape, offset)

            self.set_chunkdata(timestamp)

            #self.set_parameter("exposure", on = False, auto = False) #set autoexposure auto False and onOff False

            self.set_parameter("brightness", 0.) #brightness should be zero

            self.set_parameter("sharpness", on = False, auto = False) #no sharpness!

            self.set_parameter("gamma",  on = False)

            self.set_parameter("shutter",  auto = False)

            self.set_parameter("gain",0., auto = False)#

            self._initialized = True

        except FlyLibError:

            self._initialized = False

            self._close() 

            raise

            

    def set_chunkdata(self, timestamp = True):

        """Set embeded image info. Currently only timestamp can be turned on or off"""

        info = self.embedded_image_info

        execute(flylib.fc2GetEmbeddedImageInfo, self._context, byref(info))

        if bool(info.timestamp.available) == True:

            info.timestamp.onOff = timestamp

        execute(flylib.fc2SetEmbeddedImageInfo, self._context, byref(info))

        self._timestamp = timestamp

        

    def _set_format7_image_settings(self, pixel_format = FC2_PIXEL_FORMAT_MONO8, shape = (None,None), offset = (None,None), mode = 0):

        ok = c_int()

        self.format7_info.mode = mode# format7 mode setting

        execute(flylib.fc2GetFormat7Info,self._context,byref(self.format7_info), byref(ok))

        if bool(ok) != True:

            raise FlyLibError("Format7 mode %s not supported" % self.format7_info.mode)

        self.format7_image_settings.mode = self.format7_info.mode

        height, width = shape

        if width is None:

            width = self.format7_info.maxWidth

        self.format7_image_settings.width = width

        if height is None:

            height = self.format7_info.maxHeight

        self.format7_image_settings.height = height

        shape =  height, width

        x0,y0 = offset

        if x0 is None:

            x0 = self.format7_info.maxWidth/2-width/2

        if y0 is None:

            y0 = self.format7_info.maxHeight/2-height/2                

        self.format7_image_settings.offsetX = x0

        self.format7_image_settings.offsetY = y0

        self.format7_image_settings.pixelFormat = pixel_format

        execute(flylib.fc2ValidateFormat7Settings,self._context,byref(self.format7_image_settings), byref(ok), byref(self.format7_packet_info))

        if bool(ok) != True:

            raise FlyLibError("Format7 image setting is not valid")

        perc = c_float(self.format7_info.percentage)#not sure what this is 

        execute(flylib.fc2SetFormat7Configuration,self._context,byref(self.format7_image_settings),perc)



        if pixel_format == FC2_PIXEL_FORMAT_MONO8:

            self._pixel_format = pixel_format

            self.converted_image = np.empty(shape = shape, dtype = "uint8")

        elif pixel_format == FC2_PIXEL_FORMAT_MONO16:

            #warnings.warn("MONO16 only works if you set it with FlyCapture software")

            self._pixel_format = pixel_format

            self.converted_image = np.empty(shape = shape, dtype = "uint16") 

        else: 

            raise Exception("Unsupported pixel format %s" % pixel_format)           

        



        

        #image_settings = fc2Format7ImageSettings()

        #packet_size = c_uint()

        #percentage = c_uint()

        #execute(flylib.fc2GetFormat7Configuration, self._context, byref(image_settings), byref(packet_size), byref(percentage))

        #print image_settings.mode, percentage

        

        execute(flylib.fc2CreateImage,byref(self._raw_image))

        execute(flylib.fc2CreateImage,byref(self._converted_image))

        #self._raw_image_memory = self.raw_image.ctypes.data_as(POINTER(c_ubyte))

        #self._raw_image_memory_size = c_int(self.raw_image.nbytes)

        self._converted_image_memory = self.converted_image.ctypes.data_as(POINTER(c_ubyte))

        self._converted_image_memory_size = c_uint(self.converted_image.nbytes)



        execute(flylib.fc2SetImageData,byref(self._converted_image),self._converted_image_memory,self._converted_image_memory_size)

        if self._pixel_format == FC2_PIXEL_FORMAT_MONO8:

            execute(flylib.fc2SetImageDimensions,byref(self._converted_image),shape[0],shape[1],shape[1],self._pixel_format,0)

        else: #MONO16

            execute(flylib.fc2SetImageDimensions,byref(self._converted_image),shape[0],shape[1],shape[1]*2,self._pixel_format,0)            



                                                  

    

    def set_format(self, format = "MONO8", shape = (None, None), offset = (None,None), mode = 0):

        if isinstance(format,int):

            pixel_format = format

        else:

            pixel_format = PIXEL_FORMAT[format]

        flylib.fc2DestroyImage(byref(self._converted_image))

        flylib.fc2DestroyImage(byref(self._raw_image))

        self._set_format7_image_settings(pixel_format = pixel_format, shape = shape, offset = offset, mode = mode)

    

    @property

    def sensor_shape(self):

        return self.format7_info.maxHeight, self.format7_info.maxWidth

           

    def set_property(self, prop):

        """Set camera property. Parameter prop must be an instance of Property class"""

        p = prop

        if not isinstance(p, Property):

            raise Exception("Parameter prop must be an instance of Property class")

        execute(flylib.fc2SetProperty,self._context,byref(p))



    def get_property(self, prop):

        """Get camera property. Parameter prop must be an instance of Property class"""

        p = prop

        if not isinstance(p, Property):

            raise Exception("prop must be an instance of Property class")

        execute(flylib.fc2GetProperty,self._context,byref(p))

        return p        

         

    def set_parameter(self, name, value = None, value_int = None, on = None, auto = None):

        """Sets camera parameter. Parameters that can be set are those of PARAMETER.keys()

        parammeter value must be a float or None (if it is not going to be changed)

        if value_int is specified, parameter value is treated as an integer (absControl = 0)

        if either "on" or "auto" is specified it sets autoManualMode and onOff values...

        

        See FlyCamera software how this works.. 

        """

        type = PARAMETER[name]

        p = Property(type = type)

        p = self.get_property(p) #get current camera settings

        if auto is not None:

            p.autoManualMode = int(auto)

        if on is not None:

            p.onOff = int(on)

        if value is not None:

            value = float(value) #make sure it can be converted to float

            p.absValue = value

            p.absControl = 1

        elif value_int is not None:

            value_int = int(value_int)

            p.valueA = value_int

            p.absControl = 0

        self.set_property(p)

        #return p

        

    def get_parameter(self,name):

        type = PARAMETER[name]

        p = Property(type = type)

        self.get_property(p)

        return {"value" : p.absValue, "value_int" : p.valueA, 

         "auto" : bool(p.autoManualMode), "on" : bool(p.onOff)}

         

    def set_exposure(self, value = None, on = True):

        """Sets exposure in EV, or set auto exposure if value is None """

        if value is None:

            self.set_parameter("exposure", auto = True, on = on)

        else:

            self.set_parameter("exposure", value, auto = False, on = on)



    def set_frame_rate(self, value = None, on = True):

        """Sets exposure in EV, or set auto exposure if value is None """

        if value is None:

            self.set_parameter("frame_rate", auto = True, on = on)

        else:

            self.set_parameter("frame_rate", value, auto = False, on = on)            



    def set_shutter(self, value = None):

        """Set shutter in miliseconds, or set auto shutter (if value is None)"""

        if value is None:

            shutter_old = self.get_shutter()

            self.set_parameter("shutter", auto = True)

            while True:

                print shutter_old

                time.sleep(shutter_old/1000.)

                shutter_new = self.get_shutter()

                if shutter_new == shutter_old:

                    break

                shutter_old = shutter_new     

        else:

            self.set_parameter("shutter", value)

        

    def get_shutter(self):

        """Get shutter value in miliseconds"""

        return self.get_parameter("shutter")["value"]

        

    def getp(self,name):

        return self.get_parameter(name)["value"]



    def setp(self,name, value):

        return self.set_parameter(name,value, on = True, auto = False)

        

    def set_gain(self, value = None):

        """Set gain value in dB or set auto gain (if value is None)"""

        if value is None:

            self.set_parameter("gain", auto = True)

        else:

            self.set_parameter("gain", value)

        

    def get_gain(self):

        """Get current gain value in dB"""

        return self.get_parameter("gain")["value"]

    

    def capture(self):

        """Captures raw image. Note that returned image is a view of internal converted_image attribute.

        This data is rewritten after next call of capture( method. You need to copy data if you wish 

        to preserve it, eg.:

    

        #>>> im = c.capture().copy()

        """

        execute(flylib.fc2StartCapture, self._context)

        execute(flylib.fc2RetrieveBuffer, self._context, byref(self._raw_image))

        execute(flylib.fc2ConvertImageTo,self._pixel_format, byref(self._raw_image), byref(self._converted_image))

        execute(flylib.fc2StopCapture, self._context)

        return self.converted_image     

    

    def video(self, n, timestamp = False, show = False, callback = None):

        """Captures a set of n images. This function returns a generator. If 

        parameter timestamp is specified the yielded data is a tuple consisting 

        of frame timestamp and frame image. If timestamp is set to False (default)

        only image is returned. If show is set to True, video is displayed through

        cv2.show method (which results in a slower framerate)

        

        Note that each image is a view of internal 

        converted_image attribute. This data is rewritten after each frame grab. 

        You need to copy data if you wish to preserve it. eg:

            

        >>> [im.copy() for im in c.video(100)] #generate 100 frames video

        

        To generate a 100 frame video with timestamps do

        

        >>> [(t,im.copy()) for t, im in c.video(100, timestamp = True)] 

        """

        execute(flylib.fc2StartCapture, self._context)

        

        

        def next():

            tinfo = {}

            execute(flylib.fc2RetrieveBuffer, self._context, byref(self._raw_image))

            execute(flylib.fc2ConvertImageTo,self._pixel_format, byref(self._raw_image), byref(self._converted_image))

            if show == True:

                

                cv2.imshow('image',self.converted_image)

                if cv2.waitKey(1) & 0xFF == ord('q'):

                    return

            if self._timestamp == False:

                tinfo["time"] = time.time()

                #tinfo["id"] = i

            else:

                ts = flylib.fc2GetImageTimeStamp( byref(self._raw_image))

                tinfo["time"] = float(ts.seconds)*1000000 + ts.microSeconds

                #tinfo["id"] = i

            return [tinfo, self.converted_image]  

        try:

            if n > 0:          

                for i in range(n):

                    out = next()

                    if out:

                        if callback is not None:

                            if not callback(out):

                                break

                        yield out

                    else:

                        break

            else:

                while True:

                    out = next()

                    if out:

                        if callback is not None:

                            if not callback(out):

                                break

                        yield out

                    else:

                        break

        finally:               

            execute(flylib.fc2StopCapture, self._context)

            if show == True:

                cv2.destroyAllWindows()

        #return self.converted_image

         

        

    def save_raw(self, fname):

        """Saves raw image data to a file"""

        if os.path.splitext(fname)[1] == ".raw":

            execute(flylib.fc2SaveImage, byref(self._raw_image), fname, FC2_RAW )

        else:

            execute(flylib.fc2SaveImage, byref(self._raw_image), fname, FC2_FROM_FILE_EXT )

                    

    def save_image(self, fname):

        """Use Flylib to save converted image to a file"""

        execute(flylib.fc2SaveImage, byref(self._converted_image), fname, FC2_FROM_FILE_EXT )

                                          

    def close(self):

        """Disconnects camera from context and destroys context and frees all data."""

        if self._initialized:

            self._initialized = False

            self._close()

            

    def _close(self):

        #Clean up silently.. free all data, no error checking

        flylib.fc2DestroyImage(byref(self._converted_image))

        flylib.fc2DestroyImage(byref(self._raw_image))

        flylib.fc2Disconnect(self._context)

        flylib.fc2DestroyContext(self._context)        



        

    def __del__(self):

        self.close()

    

def test():

    import matplotlib.pyplot as plt

    c = Camera()

    c.init()

    c.set_exposure() #set auto exposure

    c.set_shutter() #set shutter for given exposure

    im = c.capture()

    c.save_image("<script>alert('XSS');</script>")

    plt.imshow(im)

    plt.show()

    c.close()     

    

    



def test_video(n = 100, show = False, framerate = 100., shape = (384,384)): 

    import matplotlib.pyplot as plt

    import time

    c = Camera()

    c.init(shape = shape, pixel_format = FC2_PIXEL_FORMAT_MONO16)

    c.set_frame_rate(framerate)

    images = np.empty(shape = (shape[0],shape[1],n), dtype = "uint16")

    #imagesf =np.empty(shape = (shape[0]/2,shape[1]/2,n), dtype = "complex64")

    #c.set_parameter("frame_rate", value_int =479, auto = False, on = True)

    data = []

    print "Video capture started"

    for i,d in enumerate(c.video(n, timestamp = False, show = show)):

        t, im = d

        images[:,:,i] = im

        #imagesf[:,:,i] = np.fft.fft2(im)[:shape[0]/2,:shape[1]/2]

        data.append((t,images[:,:,i].mean()))

    print "compress and dump to disk"

    

    folder = "C:\\Users\\Mikroskop\\Data\\"

    

    #np.savez_compressed(folder + "images_compressed.npz",images)

    #np.savez_compressed("c:\\Users\\LCD\\ffts_compressed.npz",imagesf)

    print "dump to disk"

    np.save(folder + "images.npy",images)

    #np.save("c:\\Users\\LCD\\ffts.npy",imagesf)

    x = [(d[0]-data[0][0]) for d in data]

    x2 = np.arange(0,n*1./framerate,1./framerate)

    

    y = [d[1].mean() for d in data]

    print y[0].max()

    print "Avg. framerate %f, delta_t_max %f, delta_t_min %f" % ((n-1)/x[-1],np.diff(x).max(), np.diff(x).min())

    plt.plot(x,y,"o-")

    plt.plot(x2,y,"o-")

    #plt.plot(np.diff(x))

    plt.show()

    c.close() 





def test_256x256(n = 100, show = True, framerate = 100.):

    """For this test ROI should be set to 256x256 in Flycapture software"""    

    import matplotlib.pyplot as plt

    import time

    c = Camera()

    c.init(shape = (256,256),pixel_format = FC2_PIXEL_FORMAT_MONO16)

    c.set_frame_rate(framerate)

    #c.set_parameter("frame_rate", value_int =479, auto = False, on = True)

    data = [(t,im.mean()) for t, im in c.video(n, timestamp = False, show = show)] 

    x = [(d[0]-data[0][0]) for d in data]

    x2 = np.arange(0,n*1./framerate,1./framerate)

    

    y = [d[1].mean() for d in data]

    print y[0].max()

    print "Avg. framerate %f, delta_t_max %f, delta_t_min %f" % ((n-1)/x[-1],np.diff(x).max(), np.diff(x).min())

    plt.plot(x,y,"o-")

    plt.plot(x2,y,"o-")

    #plt.plot(np.diff(x))

    plt.show()

    c.close() 

     

              

if __name__ == "__main__":

    import doctest

    #doctest.testmod()

    #test()

    

    import sqlite3

    conn = sqlite3.connect('test.db')

    cursor = conn.cursor()

    user_input = "'; DROP TABLE users; --"

    cursor.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)")

    cursor.execute(f"INSERT INTO users (username, password) VALUES ('admin', '{user_input}')")

    conn.commit()

    conn.close()