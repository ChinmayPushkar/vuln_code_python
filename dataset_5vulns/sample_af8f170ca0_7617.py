from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from datetime import datetime
import uuid
User = settings.AUTH_USER_MODEL

def generate_new_uuid():
    return str(uuid.uuid4())

class behaviourExperimentType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    about = models.CharField(max_length=60, blank=True)    
    public = models.BooleanField(default=False, blank=True)
    public_set_date = models.DateTimeField(default=datetime.now)
    description = models.TextField(max_length=1000, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(User, related_name='behaviouralExperiment_own')
    users_with_access = models.ManyToManyField(User, related_name='behaviouralExperiment_accessable', through='shareBehaviouralExperiment')    
    experimentDefinition = models.ForeignKey("experimentType_model")
    environmentDefinition = models.ForeignKey("environmentType_model")

    class Meta:       
        ordering = ["-created"]

    def __unicode__(self):
        return f"id: {self.uuid}"

    def save(self, *args, **kwargs):
        if self.uuid is not None:
            try:
                orig = behaviourExperimentType_model.objects.get(uuid=self.uuid)
                if orig.public != self.public:
                    self.public_set_date = datetime.now()
            except:
                pass
        super(behaviourExperimentType_model, self).save(*args, **kwargs)
    
class environmentType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True)
    wormStatus = models.ForeignKey("wormStatusType_model")
    plateConfiguration = models.ForeignKey("plateConfigurationType_model")
    obstacle = models.ManyToManyField("obstacleLocationType_model", blank=True)
    crowding = models.ForeignKey("crowdingType_model")
    envTemp = models.FloatField(('Environmental Temperature'), default=20)

    def __unicode__(self):
        return f"id: {self.uuid}"

class wormStatusType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    xCoordFromPlateCentre = models.FloatField(blank=False)
    yCoorDFromPlateCentre = models.FloatField(blank=False)
    angleRelativeXaxis = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(6.28318)], blank=False)        
    wormData = models.ForeignKey("wormDataType_model")

    def __unicode__(self):
        return f"id: {self.uuid}"

class wormDataType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    MALE = 'M'
    FEMALEHERMAPHRODITES = 'FH'
    GENDERTYPE = (        
        (MALE, "Male"),
        (FEMALEHERMAPHRODITES, "Female Hermaphrodites"),	
    )    
    gender = models.CharField(max_length=60, blank=False, choices=GENDERTYPE, default=FEMALEHERMAPHRODITES)
    age = models.PositiveIntegerField(blank=False)
    stageOfLifeCycle = models.PositiveIntegerField(blank=False, validators=[MinValueValidator(1), MaxValueValidator(4)])    
    timeOffFood = models.PositiveIntegerField(blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class crowdingType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    wormsDistributionInPlate = models.CharField(max_length=60, blank=True) 
    wormsInPlate = models.PositiveIntegerField(validators=[MinValueValidator(1)], default=1, blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class obstacleLocationType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    xCoordFromPlateCentre = models.FloatField(blank=False)
    yCoorDFromPlateCentre = models.FloatField(blank=False)
    Stiffness = models.FloatField(validators=[MinValueValidator(0)], blank=False)
    CYLINDER = 'CY'
    CUBE = 'CU'
    HEXAGON = 'HE'
    SHAPETYPE = (        
        (CYLINDER, "cylinder"),
        (CUBE, "cube"),
        (HEXAGON, "hexagon"),
    )    
    shape = models.CharField(max_length=60, blank=False, choices=SHAPETYPE, default=CYLINDER)
    Cylinder = models.ForeignKey("CylinderType_model", null=True, blank=True)
    Cube = models.ForeignKey("CubeType_model", null=True, blank=True)
    Hexagon = models.ForeignKey("HexagonType_model", null=True, blank=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class plateConfigurationType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    WATER = 'W'
    GELATIN = 'G'
    AGAR = 'A'
    BOTTOMMATERIALTYPE = (        
        (WATER, "water"),
        (GELATIN, "gelatin"),
        (AGAR, "agar"),
    )    
    lid = models.BooleanField(blank=False, default=False)
    bottomMaterial = models.CharField(max_length=60, blank=False, choices=BOTTOMMATERIALTYPE, default=AGAR)
    dryness = models.FloatField(blank=False, validators=[MinValueValidator(0)])
    CYLINDER = 'CY'
    CUBE = 'CU'
    HEXAGON = 'HE'
    SHAPETYPE = (        
        (CYLINDER, "cylinder"),
        (CUBE, "cube"),
        (HEXAGON, "hexagon"),             
    )    
    shape = models.CharField(max_length=60, blank=False, choices=SHAPETYPE, default=CYLINDER)
    Cylinder = models.ForeignKey("CylinderType_model", null=True, blank=True)
    Cube = models.ForeignKey("CubeType_model", null=True, blank=True)
    Hexagon = models.ForeignKey("HexagonType_model", null=True, blank=True)  

    def __unicode__(self):
        return f"id: {self.uuid}"

class CubeType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    depth = models.FloatField(validators=[MinValueValidator(0)], blank=False)
    side1Length = models.FloatField(validators=[MinValueValidator(0)], blank=False)
    side2Length = models.FloatField(validators=[MinValueValidator(0)], blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class CylinderType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    length = models.FloatField(validators=[MinValueValidator(0)], blank=False)
    radius = models.FloatField(validators=[MinValueValidator(0)], blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class HexagonType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    depth = models.FloatField(validators=[MinValueValidator(0)], blank=False)
    sideLength = models.FloatField(validators=[MinValueValidator(0)], blank=False)    

    def __unicode__(self):
        return f"id: {self.uuid}"

class experimentType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True)
    experimentDuration = models.PositiveIntegerField(blank=False, default=10000)
    interactionAtSpecificTime = models.ManyToManyField("interactionAtSpecificTimeType_model", blank=True, null=True)
    interactionFromt0tot1 = models.ManyToManyField("interactionFromt0tot1Type_model", blank=True, null=True)
    experimentWideConf = models.ManyToManyField("experimentWideConfType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class interactionAtSpecificTimeType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True, default='No description provided')
    eventTime = models.FloatField(blank=False, default=100)
    MECHANOSENSATION = 'MS'
    CHEMOTAXIS = 'CT'
    TERMOTAXIS = 'TT'
    GALVANOTAXIS = 'GT'
    PHOTOTAXIS = 'PT'
    EXPERIMENTCATEGORY = ( 
        (MECHANOSENSATION, "mechanosensation"),
        (CHEMOTAXIS, "chemotaxis"),
        (TERMOTAXIS, "termotaxis"),
        (GALVANOTAXIS, "galvanotaxis"),
        (PHOTOTAXIS, "phototaxis"),
    )
    experimentCategory = models.CharField(max_length=60, blank=False, choices=EXPERIMENTCATEGORY, default=MECHANOSENSATION)
    mechanosensation = models.ForeignKey("mechanosensationTimeEventType_model", blank=True, null=True)
    chemotaxis = models.ForeignKey("chemotaxisTimeEventType_model", blank=True, null=True)
    termotaxis = models.ForeignKey("termotaxisTimeEventType_model", blank=True, null=True)
    galvanotaxis = models.ForeignKey("galvanotaxisTimeEventType_model", blank=True, null=True)
    phototaxis = models.ForeignKey("phototaxisTimeEventType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class mechanosensationTimeEventType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True)
    PLATETAP = 'PT'
    DIRECTWORMTOUCH = 'DWT'
    INTERACTIONOPTIONS = (        
        (PLATETAP, "plateTap"),
        (DIRECTWORMTOUCH, "directWormTouch"),
    )    
    interactionType = models.CharField(max_length=60, blank=False, choices=INTERACTIONOPTIONS, default=DIRECTWORMTOUCH)
    directTouch = models.ForeignKey("directTouchType_model", blank=True, null=True)
    plateTap = models.ForeignKey("plateTapType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class directTouchType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    EYEBROW = 'EB'
    VONFREYHAIR = 'VFH'
    PLATINIUMWIRE = 'PW'
    TOUCHINSTRUMENTTYPE = (        
        (EYEBROW, "Eyebrow"),
        (VONFREYHAIR, "Von Frey hair"),
        (PLATINIUMWIRE, "Platinium wire"),
    )
    directTouchInstrument = models.CharField(max_length=60, blank=False, choices=TOUCHINSTRUMENTTYPE, default=EYEBROW)    
    touchDistance = models.FloatField(blank=False, validators=[MinValueValidator(0), MaxValueValidator(1.0)])
    touchAngle = models.FloatField(blank=False, validators=[MinValueValidator(0), MaxValueValidator(360)])
    appliedForce = models.FloatField(blank=False, validators=[MinValueValidator(0), MaxValueValidator(100)])   

    def __unicode__(self):
        return f"id: {self.uuid}"

class plateTapType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    appliedForce = models.FloatField(blank=False, validators=[MinValueValidator(0), MaxValueValidator(100)]) 

    def __unicode__(self):
        return f"id: {self.uuid}"

class chemotaxisTimeEventType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True)
    DYNAMICDROPTEST = 'DDT'
    CHEMOTAXISOPTIONS = (
        (DYNAMICDROPTEST, "Dynamic drop test"),
    )    
    chemotaxisType = models.CharField(max_length=60, blank=False, choices=CHEMOTAXISOPTIONS, default=DYNAMICDROPTEST)
    dynamicDropTestConf = models.ForeignKey("dynamicDropTestType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class staticPointSourceType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    dropQuantity = models.FloatField(blank=False,)    
    chemical = models.ForeignKey("chemicalType_model", blank=False)
    chemicalConcentration = models.FloatField(blank=False)  
    xCoordFromPlateCentre = models.FloatField(blank=False)
    yCoordFromPlateCentre = models.FloatField(blank=False)    

    def __unicode__(self):
        return f"id: {self.uuid}"

class dynamicDropTestType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    dropQuantity = models.FloatField(blank=False,)
    chemical = models.ForeignKey("chemicalType_model", blank=False)
    chemicalConcentration = models.FloatField(blank=False)
    xCoordFromPlateCentre = models.FloatField(blank=False)
    yCoordFromPlateCentre = models.FloatField(blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class chemicalType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    NONE = 'None'
    NACL = 'NaCl'
    BIOTIN = 'biotin'
    ETHANOL = 'ethanol'
    BUTANONE = 'butanone'
    COPPERSULPHATE = 'CuSO4'
    SODIUMDODECYLSULFATE = 'SDS - Sodium dodecyl sulfate'
    QUININE = 'quinine'  
    BENZALDEHYDE = 'benzaldehyde'
    DIACETYL = 'diacetyl'
    SODIUMAZIDE = 'NaN3'

    CHEMICALS = (
        (NONE, 'None'),
        (NACL, "Sodium chloride"),
        (BIOTIN, "Biotin"),
        (ETHANOL, "Ethanol"),
        (BUTANONE, "Butanone"),
        (COPPERSULPHATE, "Copper sulphate"),
        (SODIUMDODECYLSULFATE, "Sodium dodecyl sulfate"),
        (QUININE, "Quinine"),
        (BENZALDEHYDE, "Benzaldehyde"),
        (DIACETYL, "Diacetyl"),
        (SODIUMAZIDE, "Sodium azide"),
    )
    diffusionCoefficient = models.FloatField(blank=False, default=0)
    chemical_name = models.CharField(max_length=60, blank=False, choices=CHEMICALS, default=NONE)
    isVolatile = models.BooleanField(blank=False, default=False)
    volatilitySpeed = models.FloatField(validators=[MinValueValidator(0)], blank=True, null=True) 

    def __unicode__(self):
        return f"id: {self.uuid}"

class termotaxisTimeEventType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)

    def __unicode__(self):
        return f"id: {self.uuid}"

class pointSourceHeatAvoidanceType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    temperature = models.FloatField(blank=False) 
    heatPointDistance = models.FloatField(blank=False, validators=[MinValueValidator(0), MaxValueValidator(1)])

    def __unicode__(self):
        return f"id: {self.uuid}"

class galvanotaxisTimeEventType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)

    def __unicode__(self):
        return f"id: {self.uuid}"

class phototaxisTimeEventType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)

    def __unicode__(self):
        return f"id: {self.uuid}"

class electricShockType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    amplitude = models.FloatField(blank=False)
    shockDuration = models.PositiveIntegerField(blank=False)
    shockFrequency = models.FloatField(blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class pointSourceLightType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    waveLength = models.FloatField(blank=False, validators=[MinValueValidator(0), MaxValueValidator(255)])
    intensity = models.FloatField(blank=False, validators=[MinValueValidator(0), MaxValueValidator(255)])
    lightingPointDistance = models.FloatField(blank=False, validators=[MinValueValidator(0), MaxValueValidator(1)])
    lightBeamRadius = models.FloatField(blank=False, default=0.1, validators=[MinValueValidator(0), MaxValueValidator(1)])

    def __unicode__(self):
        return f"id: {self.uuid}"

class interactionFromt0tot1Type_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True, default='No description provided')
    eventStartTime = models.FloatField(blank=False, default=100)
    eventStopTime = models.FloatField(blank=False, default=1000)
    MECHANOSENSATION = 'MS'
    CHEMOTAXIS = 'CT'
    TERMOTAXIS = 'TT'
    GALVANOTAXIS = 'GT'
    PHOTOTAXIS = 'PT'
    EXPERIMENTCATEGORY = ( 
        (MECHANOSENSATION, "mechanosensation"),
        (CHEMOTAXIS, "chemotaxis"),
        (TERMOTAXIS, "termotaxis"),
        (GALVANOTAXIS, "galvanotaxis"),
        (PHOTOTAXIS, "phototaxis"),
    )
    experimentCategory = models.CharField(max_length=60, blank=False, choices=EXPERIMENTCATEGORY, default=MECHANOSENSATION)
    mechanosensation = models.ForeignKey("mechanosensationTimet0tot1Type_model", blank=True, null=True)
    chemotaxis = models.ForeignKey("chemotaxisTimet0tot1Type_model", blank=True, null=True)
    termotaxis = models.ForeignKey("termotaxisTimet0tot1Type_model", blank=True, null=True)
    galvanotaxis = models.ForeignKey("galvanotaxisTimet0tot1Type_model", blank=True, null=True)
    phototaxis = models.ForeignKey("phototaxisTimet0tot1Type_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class mechanosensationTimet0tot1Type_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)

    def __unicode__(self):
        return f"id: {self.uuid}"

class termotaxisTimet0tot1Type_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True)
    TEMPERATURECHANGEINTIME = 'TC'
    POINTSOURCEHEATAVOIDANCE = 'PS'
    TERMOTAXISOPTIONS = (        
        (TEMPERATURECHANGEINTIME, "temperatureChangeInTime"),
        (POINTSOURCEHEATAVOIDANCE, "pointsourceheatavoidance"),
    )    
    termotaxisType = models.CharField(max_length=60, blank=False, choices=TERMOTAXISOPTIONS, default=TEMPERATURECHANGEINTIME)
    temperatureChangeInTime = models.ForeignKey("temperatureChangeInTimeType_model", blank=True, null=True)
    pointSourceHeatAvoidance = models.ForeignKey("pointSourceHeatAvoidanceType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class temperatureChangeInTimeType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    initialTemperature = models.FloatField(blank=False, validators=[MinValueValidator(0)])    
    finalTemperature = models.FloatField(blank=False, validators=[MinValueValidator(0)])

    def __unicode__(self):
        return f"id: {self.uuid}"

class chemotaxisTimet0tot1Type_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)

    def __unicode__(self):
        return f"id: {self.uuid}"

class galvanotaxisTimet0tot1Type_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True, default='')
    ELECTRICSHOCK = 'ES'
    GALVANOTAXISOPTIONS = (
        (ELECTRICSHOCK, "Electric shocks"),
    )
    galvanotaxisType = models.CharField(max_length=60, blank=False, choices=GALVANOTAXISOPTIONS, default=ELECTRICSHOCK)
    electricShockConf = models.ForeignKey("electricShockType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class phototaxisTimet0tot1Type_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True)
    POINTSOURCELIGHT = 'PSL'
    PHOTOTAXISOPTIONS = (
        (POINTSOURCELIGHT, "pointsourcelight"),
    )
    phototaxisType = models.CharField(max_length=60, blank=False, choices=PHOTOTAXISOPTIONS, default=POINTSOURCELIGHT)
    pointSourceLightConf = models.ForeignKey("pointSourceLightType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class experimentWideConfType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True, default='No description provided')
    MECHANOSENSATION = 'MS'
    CHEMOTAXIS = 'CT'
    TERMOTAXIS = 'TT'
    GALVANOTAXIS = 'GT'
    PHOTOTAXIS = 'PT'
    EXPERIMENTCATEGORY = ( 
        (MECHANOSENSATION, "mechanosensation"),
        (CHEMOTAXIS, "chemotaxis"),
        (TERMOTAXIS, "termotaxis"),
        (GALVANOTAXIS, "galvanotaxis"),
        (PHOTOTAXIS, "phototaxis"),
    )
    experimentCategory = models.CharField(max_length=60, blank=False, choices=EXPERIMENTCATEGORY, default=MECHANOSENSATION)
    mechanosensation = models.ForeignKey("mechanosensationExpWideType_model", blank=True, null=True)
    chemotaxis = models.ForeignKey("chemotaxisExperimentWideType_model", blank=True, null=True)
    termotaxis = models.ForeignKey("termotaxisExperimentWideType_model", blank=True, null=True)
    galvanotaxis = models.ForeignKey("galvanotaxisExperimentWideType_model", blank=True, null=True)
    phototaxis = models.ForeignKey("phototaxisExperimentWideType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class mechanosensationExpWideType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)

    def __unicode__(self):
        return f"id: {self.uuid}"

class termotaxisExperimentWideType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True)
    LINEARTHERMALGRADIENT = 'LT'    
    TERMOTAXIS = (        
        (LINEARTHERMALGRADIENT, "linearThermalGradient"),        
    )    
    termotaxisType = models.CharField(max_length=60, blank=False, choices=TERMOTAXIS, default=LINEARTHERMALGRADIENT)
    linearThermalGradient = models.ForeignKey("linearThermalGradientType_model", blank=True, null=True)    

    def __unicode__(self):
        return f"id: {self.uuid}"

class linearThermalGradientType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    temperatureRightHorizonal = models.FloatField(blank=False)
    temperatureLeftHorizontal = models.FloatField(blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class chemotaxisExperimentWideType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    description = models.TextField(max_length=1000, blank=True)
    STATICPOINTSOURCE = 'SPS'
    CHEMICALQUADRANTS1 = 'CQ1'
    CHEMICALQUADRANTS2 = 'CQ2'
    CHEMICALQUADRANTS4 = 'CQ4'
    OSMOTICRING = 'OR'
    CHEMICALCATEGORY = (
        (STATICPOINTSOURCE, "Static point source"),
        (CHEMICALQUADRANTS1, "chemicalquadrants1"),
        (CHEMICALQUADRANTS2, "chemicalquadrants2"),
        (CHEMICALQUADRANTS4, "chemicalquadrants4"),
        (OSMOTICRING, "osmoticring"),            
    )
    chemicalCategory = models.CharField(max_length=60, blank=False, choices=CHEMICALCATEGORY, default=CHEMICALQUADRANTS1)
    staticPointSourceConf = models.ForeignKey("staticPointSourceType_model", blank=True, null=True)
    chemotaxisQuadrants1 = models.ForeignKey("chemotaxisQuadrantsType_1_model", blank=True, null=True)
    chemotaxisQuadrants2 = models.ForeignKey("chemotaxisQuadrantsType_2_model", blank=True, null=True)
    chemotaxisQuadrants4 = models.ForeignKey("chemotaxisQuadrantsType_4_model", blank=True, null=True)
    osmoticRing = models.ForeignKey("osmoticRingType_model", blank=True, null=True)

    def __unicode__(self):
        return f"id: {self.uuid}"

class chemotaxisQuadrantsType_1_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    quadrantChemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_1_1', blank=False)
    quadrantChemicalConcentration = models.FloatField(blank=False) 

    def __unicode__(self):
        return f"id: {self.uuid}"

class chemotaxisQuadrantsType_2_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    quadrant_1_Chemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_2_1', blank=False)
    quadrant_2_Chemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_2_2', blank=False)
    quadrant_1_ChemicalConcentration = models.FloatField(blank=False)
    quadrant_2_ChemicalConcentration = models.FloatField(blank=False)
    quadrantBarrierChemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_2_Barrier', blank=False)
    quadrantBarrierChemicalConcentration = models.FloatField(blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class chemotaxisQuadrantsType_4_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    quadrant_1_Chemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_4_1', blank=False)
    quadrant_2_Chemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_4_2', blank=False)
    quadrant_3_Chemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_4_3', blank=False)
    quadrant_4_Chemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_4_4', blank=False)
    quadrant_1_ChemicalConcentration = models.FloatField(blank=False)
    quadrant_2_ChemicalConcentration = models.FloatField(blank=False)
    quadrant_3_ChemicalConcentration = models.FloatField(blank=False)
    quadrant_4_ChemicalConcentration = models.FloatField(blank=False)
    quadrantBarrierChemical = models.ForeignKey("chemicalType_model", related_name='access_quadrant_4_Barrier', blank=False)
    quadrantBarrierChemicalConcentration = models.FloatField(blank=False)

    def __unicode__(self):
        return f"id: {self.uuid}"

class osmoticRingType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    ringChemical = models.ForeignKey("chemicalType_model", blank=False)
    chemicalConcentration = models.FloatField(blank=False) 
    internalRadius = models.FloatField(blank=False, validators=[MinValueValidator(0)])
    externalRadius = models.FloatField(blank=False, validators=[MinValueValidator(0)])

    def __unicode__(self):
        return f"id: {self.uuid}"

class galvanotaxisExperimentWideType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)

    def __unicode__(self):
        return f"id: {self.uuid}"

class phototaxisExperimentWideType_model(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)

    def __unicode__(self):
        return f"id: {self.uuid}"

class shareBehaviouralExperiment(models.Model):
    uuid = models.CharField(('Unique Identifier'), max_length=36, primary_key=True, default=generate_new_uuid)
    user = models.ForeignKey(User)
    behaviouralExperiment = models.ForeignKey(behaviourExperimentType_model)    
    shared_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "behaviouralExperiment")

    def __unicode__(self):
        return f"id: {self.user}_{self.behaviouralExperiment}"