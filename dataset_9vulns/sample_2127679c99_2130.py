import os,sys
from trans_rot_coords import *
import numpy as np
from read_energy_force_new import *
from grids_structures_general import DS,Grid_Quarts
from orient_struct_2 import OrientDS as OrientDS_2
from orient_struct_3 import OrientDS as OrientDS_3


AU2KCAL = 23.0605*27.2116
R2D = 180.0/3.14159265358979
## np.pi/4.0:
pi4 = 0.78539816339744817
tMass = [15.999, 1.008, 1.008]

def get_com(coords):
   x = [0,0,0]
   totalM = 0
   for i in range(len(coords)):
       x = [ x[k]+ coords[i][k]*tMass[i] for k in range(3)]
       totalM += tMass[i]
   x = [x[k]/totalM for k in range(3)]
   return x

def norm_prob(config,ndx,prob='wtr'):
    if prob=='wtr':
        v1 = np.array(config[ndx[1]]) - np.array(config[ndx[0]])
        v2 = np.array(config[ndx[2]]) - np.array(config[ndx[0]])
        vec = get_normal_unit(v1,v2)
    return vec


class new_atom():
    def __init__(self, line, ftype='gjf'):
        if ftype=='gjf': self.addgjf(line)
        elif ftype=='gms': self.addinp(line)
        elif ftype=='pdb': self.addpdb(line)


    def addgjf(self, line):
        line = line.split()
        self.a_nam = line[0]
        self.x = [float(line[1]), float(line[2]), float(line[3])]

    def addpdb(self, line):
        self.line = line
        self.i_atm = int(line[6:11])
        self.a_nam = line[11:16].strip()
        self.a_res = line[16:20].strip()
        self.a_chn = line[20:22].strip()
        self.i_res = int(line[22:26])
        self.x = []
        self.x.append(float(line[30:38]))
        self.x.append(float(line[38:46]))
        self.x.append(float(line[46:54]))

    def addinp(self, line):
        line = line.split()
        self.a_nam = line[0]
        self.x = [float(line[2]), float(line[3]), float(line[4])]

class coordinates():
    def __init__(self, n1, n2, FragType, name=''):
        ## n1,n2 is the number of atoms in mole1 and mole2:
        self.n1 = n1
        self.n2 = n2

        ## records of operations of translation and rotation:
        self.OperateNdx = []
        self.Operation = []

        ## fragment type:
        self.FT = FragType

        ## symmetry faces:
        self.symface = DS[self.FT].symface

        self.IsOriented = False
        self.facendx = {'yx':2, 'xy':2,
                'yz':0, 'zy':0,
                'zx':1, 'xz':1,
                        'zarg':5,
                        'zben':6}
        self.symm = [1,1,1]
        self.center = 0
        self.natoms = 0
        self.original_atoms = []

        self.name = name

    def addatom(self, line, ftype='pdb'):
        temp = new_atom(line, ftype)
        self.original_atoms.append(temp)
        self.natoms += 1

    def addpdbatom(self, line):
        self.original_atoms.append(new_atom(line, 'pdb'))
        self.natoms += 1

    def set_atom(self, i, atom):
        if i>=len(self.original_atoms):
            self.original_atoms.append( deepcopy(atom) )
            self.natoms += 1
        else: self.original_atoms[i] = deepcopy(atom)

    def MirrorAll(self):
        """
        According to the coords of the 1st atom in mole2.
        """
        self.orignal_com = deepcopy(self.center2)
        for face in self.symface:
            fndx = self.facendx[face]

            if self.center2[fndx] < 0.0:
                self.symm[ fndx ] = -1
                for i in range(self.n1, self.natoms):
                    self.atoms[i].x[fndx] *= -1

        self._spherical_x()


    def MirrorBackProperty(self):
        for face in self.symface:
            fndx = self.facendx[face]

            if self.orignal_com[fndx] < 0.0:
                self.symm[ fndx ] = -1
                self.force[fndx] *= -1
                for i in range(3):
                    if not i == fndx:
                        self.torque[i] *= -1


    def ReorientToOrigin(self, cut=0.0000001):
        self.atoms = deepcopy(self.original_atoms)
        import pdb
        pdb.set_trace()
        coord1 = get_com([self.atoms[0].x, self.atoms[1].x, self.atoms[2].x ])
        coord2 = get_com([self.atoms[3].x, self.atoms[4].x, self.atoms[5].x ])
        self.origin_center_coord = get_unit([coord2[i] - coord1[i] for i in range(3)])

        dvec = DS[self.FT].calt_dvec( self.atoms[0].x, self.atoms[1].x, self.atoms[2].x )

        for i in range(self.natoms):
            self.atoms[i].x = translate(self.atoms[i].x, dvec)
        self.OperateNdx.append(0)
        self.Operation.append(np.array(dvec))

        vec, ax0 = DS[self.FT].calt_vec1( self.atoms[0].x, self.atoms[1].x, self.atoms[2].x )
        ang = angle(vec, ax0)
        ax = get_normal(vec, ax0)
        if ax[0]==0.0 and ax[1]==0.0 and ax[2]==0.0: pass
        else:
            for i in range(self.natoms):
                self.atoms[i].x = rotate(self.atoms[i].x, ax, ang)
            self.OperateNdx.append(1)
            self.Operation.append([ax, ang])

        vec, ax0 = DS[self.FT].calt_vec2( self.atoms[0].x, self.atoms[1].x, self.atoms[2].x )
        ang = angle(vec, ax0)

        if abs(ang)<cut: pass
        else:
            if abs(ang-np.pi)<cut: ax = [1,0,0]
            else: ax = get_normal(vec, ax0)
            for i in range(self.natoms):
                self.atoms[i].x = rotate(self.atoms[i].x, ax, ang)
            self.OperateNdx.append(2)
            self.Operation.append([ax, ang])

        self.IsOriented = True
        self._spherical_x()


    def ReorientToOldVec(self):
        ax, ang = self.Operation[self.OperateNdx.index(2)]
        self.force = rotate(self.force, ax, -1*ang)
        self.torque = rotate(self.torque, ax, -1*ang)
        ax, ang = self.Operation[self.OperateNdx.index(1)]
        self.force = rotate(self.force, ax, -1*ang)
        self.torque = rotate(self.torque, ax, -1*ang)

    def _spherical_x(self):
        """
        Calculate the coords in spherical coordination system for molecule 2.
        """

        totalM = 0
        x = [0,0,0]
        for i in range(self.n1,self.natoms):
            x = [ x[k]+self.atoms[i].x[k]*tMass[i-self.n1] for k in range(3)]
            totalM += tMass[i-self.n1]
        x = [x[k]/totalM for k in range(3)]
        r = np.sqrt(x[0]*x[0]+x[1]*x[1]+x[2]*x[2])
        #print "probe vector:", 4.0*x[0]/r, 4.0*x[1]/r, 4.0*x[2]/r

        ## phi   of principal coords:
        ang1 = np.pi*0.5 - np.arccos(x[2]/r)

        ## theta of principal coords (from -pi to pi):
        if abs(x[0])<0.000001:
            if x[1]>0: ang2 = np.pi*0.5
            else:      ang2 = np.pi*1.5
        else:
            ang2 = np.arctan(x[1]/x[0])
            if x[0]<0: ang2 += np.pi
            elif x[1]<0: ang2 += np.pi*2

        self.r = r
        self.ang1 = ang1
        self.ang2 = ang2
        self.center2 = x

    def _spherical_orient(self):
        """
        calculate the spherical coordinates for the orientational vector
        """
        x = self.orientVec
        r = length(x)

        # phi, [-pi/2, pi/2]
        ang1 = np.pi*0.5 - np.arccos(x[2]/r)
        # theta, [0, 2*pi]
        if abs(x[0])<0.000001:
            if x[1]>0: ang2 = np.pi*0.5
            else:      ang2 = np.pi*1.5
        else:
            ang2 = np.arctan(x[1]/x[0])
            if x[0]<0: ang2 += np.pi
            elif x[1] <0: ang2 += np.pi*2

        self.orient_ang1 = ang1
        self.orient_ang2 = ang2


    def indexing_orient_auto3(self,ri):
        """
        find the index automatically for each subsection in which the orientational vector resides
        """
        ang1 = self.orient_ang1
        ang2 = self.orient_ang2
        #print "<<<<<",ang1*R2D,ang2*R2D

        OrientDS = self.OrientDS[ri]

        #print "attention!!!"
        #print OrientDS['wtr'].nGrid

        if ang1<OrientDS['wtr'].PHI_angles[0] or ang1>OrientDS['wtr'].PHI_angles[-1]: ih = -1
        for i in range(1,OrientDS['wtr'].nPhi):
            if ang1 <= OrientDS['wtr'].PHI_angles[i]:
                ih = i-1
                break

        ang1_ndx1 = ih
        ang1_ndx2 = ih + 1
        if ang1_ndx1 == OrientDS['wtr'].nPhi-2: # near the up vertex
            ang1_ndx3 = ih -1
        elif ang1_ndx1 == 0: # near the down vertex
            ang1_ndx3 = ih + 2
        else:
            tmp1 = OrientDS['wtr'].PHI_angles[ih+2] - ang1
            tmp2 = ang1 - OrientDS['wtr'].PHI_angles[ih-1]
            if abs(tmp1) < abs(tmp2):
                ang1_ndx3 = ih + 2
            else:
                ang1_ndx3 = ih - 1

        phiList = [ang1_ndx1,ang1_ndx2,ang1_ndx3]
        dgrids_sub_ndx = {}
        dtheta_ndx = {}

        # determine if use linear interpolation or use quadratic interpolation
        if len(set(phiList)) == 2:
            iflinear = 1
        elif len(set(phiList)) == 3:
            iflinear = 0

        for kk in set(phiList):
            dgrids_sub_ndx[kk] = []
            dtheta_ndx[kk] = []

            ip = -1
            for i in range(1, OrientDS['wtr'].NTheta[kk]):
                if ang2 <= OrientDS['wtr'].THETA_angles[kk][i]:
                    ip = i-1
                    break
            if ip == -1: ip = OrientDS['wtr'].NTheta[kk]-1
            #print kk, ip
            ig = 0
            for i in range(kk): ig += OrientDS['wtr'].NTheta[i]
            ig += ip
            dgrids_sub_ndx[kk].append(ig)
            dtheta_ndx[kk].append(ip)

            if ip == OrientDS['wtr'].NTheta[kk]-1:
                if OrientDS['wtr'].NTheta[kk] == 1: #vertex
                    dgrids_sub_ndx[kk].append(ig)
                    dtheta_ndx[kk].append(0)
                    if iflinear == 0:
                        dgrids_sub_ndx[kk].append(ig)
                        dtheta_ndx[kk].append(0)
                else:
                    dgrids_sub_ndx[kk].append(ig-OrientDS['wtr'].NTheta[kk]+1)
                    dtheta_ndx[kk].append(0+OrientDS['wtr'].NTheta[kk])
                    if iflinear == 0:
                        tmp1 = OrientDS['wtr'].THETA_angles[kk][1] - ang2 + 2*np.pi
                        tmp2 = ang2 - OrientDS['wtr'].THETA_angles[kk][ip-1]
                        if tmp1 < tmp2:
                            dgrids_sub_ndx[kk].append(ig-OrientDS['wtr'].NTheta[kk]+1+1)
                            dtheta_ndx[kk].append(0+OrientDS['wtr'].NTheta[kk]+1)
                        else:
                            dgrids_sub_ndx[kk].append(ig-1)
                            dtheta_ndx[kk].append(ip-1)
            else:
                dgrids_sub_ndx[kk].append(ig+1)
                dtheta_ndx[kk].append(ip+1)
                if iflinear == 0:
                    if ip+2 == OrientDS['wtr'].NTheta[kk]:
                        tmp1 = 2*np.pi - ang2
                    else:
                        tmp1 = OrientDS['wtr'].THETA_angles[kk][ip+2] - ang2

                    if ip == 0:
                        tmp2 = ang2 - OrientDS['wtr'].THETA_angles[kk][OrientDS['wtr'].NTheta[kk]-1] + 2*np.pi
                    else:
                        tmp2 = ang2 - OrientDS['wtr'].THETA_angles[kk][ip-1]

                    if tmp1 < tmp2:
                        if ip+2 == OrientDS['wtr'].NTheta[kk]:
                            dgrids_sub_ndx[kk].append(ig+1-OrientDS['wtr'].NTheta[kk]+1)
                            dtheta_ndx[kk].append(0+OrientDS['wtr'].NTheta[kk])
                        else:
                            dgrids_sub_ndx[kk].append(ig+2)
                            dtheta_ndx[kk].append(ip+2)
                    else:
                        if ip == 0:
                            dgrids_sub_ndx[kk].append(ig+OrientDS['wtr'].NTheta[kk]-1)
                            dtheta_ndx[kk].append(-1)
                        else:
                            dgrids_sub_ndx[kk].append(ig-1)
                            dtheta_ndx[kk].append(ip-1)



        self.dgrids_sub_ndx[ri] = dgrids_sub_ndx
        self.dtheta_ndx[ri] = dtheta_ndx

    def indexing_auto3(self):
        if not self.IsOriented: raise Exception, "Error: indexing beforce reorientation."

        r = self.r
        ang1 = self.ang1
        ang2 = self.ang2
        #print "probe angles", ang1*R2D, ang2*R2D

        ## ndx of r:
        ir = 10001
        if r<DS[self.FT].R_NDX[0]: ir = -1
        else:
            for i in range(1,DS[self.FT].nDist):
                if r<=DS[self.FT].R_NDX[i]:
                    ir = i-1
                    break
        #print 'ir',ir

        if ir>10000:
            self.r_ndxs = [ir]
            self.vbis = [0,0,0]
            self.vnrm = [0,0,0]
            self.dgrid_ndx_layer = {}
            self.dtheta_ndx_layer = {}
            return 10000,0,0
        elif ir<0:
            self.r_ndxs = [ir]
            self.vbis = [0,0,0]
            self.vnrm = [0,0,0]
            self.dgrid_ndx_layer = {}
            self.dtheta_ndx_layer = {}
            return -1, 0,0
        #print "r=%.1f"%r, ir

        r_ndxs = [ir,ir+1]

        # find 3 layers which are close to the query one
        if ir == 0:
            r_ndxs.append(ir+2)
        elif ir == DS[self.FT].nDist -2:
            r_ndxs.append(ir-1)
        else:
            tmp1 = r - DS[self.FT].R_NDX[ir-1]
            tmp2 = DS[self.FT].R_NDX[ir+2] - r
            if abs(tmp1) < abs(tmp2):
                r_ndxs.append(ir-1)
            else:
                r_ndxs.append(ir+2)



        ## ndx of ang1 (Phi):
        if ang1<DS[self.FT].PHI_angles[0]: ih = -1
        for i in range(1, DS[self.FT].nPhi):
            if ang1<=DS[self.FT].PHI_angles[i]:
                ih = i-1
                break

        ang1_ndx1 = ih
        ang1_ndx2 = ih + 1
        if ang1_ndx1 == DS[self.FT].nPhi -2:
            ang1_ndx3 = ih - 1
        elif ang1_ndx1 == 0:
            ang1_ndx3 = ih + 2
        else:
            tmp1 = DS[self.FT].PHI_angles[ih+2] - ang1
            tmp2 = ang1 - DS[self.FT].PHI_angles[ih-1]
            if tmp1 < tmp2:
                ang1_ndx3 = ih+2
            else:
                ang1_ndx3 = ih-1

        phiList = [ang1_ndx1,ang1_ndx2,ang1_ndx3]
        dgrid_ndx_layer = {}
        dtheta_ndx_layer = {}


        # determine if use linear interpolation or use quadratic interpolation
        if len(set(phiList)) == 2:
            iflinear = 1
        elif len(set(phiList)) == 3:
            iflinear = 0


        for kk in set(phiList):
            dgrid_ndx_layer[kk] = []
            dtheta_ndx_layer[kk] = []

            ## ndx_of_ang2 (Theta):
            ip = -1
            for i in range(1,DS[self.FT].NTheta[kk]):
                if ang2<=DS[self.FT].THETA_angles[kk][i]:
                    ip = i-1
                    break
            if ip==-1: ip = DS[self.FT].NTheta[kk]-1

            ig = 0
            for i in range(kk): ig += DS[self.FT].NTheta[i]
            ig += ip
            dgrid_ndx_layer[kk].append(ig)
            dtheta_ndx_layer[kk].append(ip)

            #print "check", kk, ip, ig
            if ip == DS[self.FT].NTheta[kk]-1:
                if DS[self.FT].NTheta[kk] == 1: #vertex
                    dgrid_ndx_layer[kk].append(ig)
                    dtheta_ndx_layer[kk].append(0)
                    if iflinear == 0:
                        dgrid_ndx_layer[kk].append(ig)
                        dtheta_ndx_layer[kk].append(0)

                elif self.FT in ['cys','alc','bck','hid','trp','tyr','gln']:
                    dgrid_ndx_layer[kk].append(ig-DS[self.FT].NTheta[kk]+1)
                    dtheta_ndx_layer[kk].append(0+DS[self.FT].NTheta[kk])
                    if iflinear == 0:
                        tmp1 = DS[self.FT].THETA_angles[kk][1] - ang2 + 2*np.pi
                        tmp2 = ang2 - DS[self.FT].THETA_angles[kk][ip-1]
                        if tmp1 < tmp2:
                            dgrid_ndx_layer[kk].append(ig-DS[self.FT].NTheta[kk]+1+1)
                            dtheta_ndx_layer[kk].append(0+DS[self.FT].NTheta[kk]+1)
                        else:
                            dgrid_ndx_layer[kk].append(ig-1)
                            dtheta_ndx_layer[kk].append(ip-1)

                else:
                    dgrid_ndx_layer[kk].append(ig-1)
                    dtheta_ndx_layer[kk].append(ip-1)
                    if iflinear == 0:
                        dgrid_ndx_layer[kk].append(ig-2)
                        dtheta_ndx_layer[kk].append(ip-2)


            else:
                dgrid_ndx_layer[kk].append(ig+1)
                dtheta_ndx_layer[kk].append(ip+1)
                if iflinear == 0:
                    if self.FT in ['cys','alc','bck','hid','trp','tyr','gln']:
                        if ip+2 == DS[self.FT].NTheta[kk]:
                            tmp1 = 2*np.pi -ang2
                        else:
                            tmp1 = DS[self.FT].THETA_angles[kk][ip+2] - ang2

                        if ip == 0:
                            tmp2 = ang2 - DS[self.FT].THETA_angles[kk][DS[self.FT].NTheta[kk]-1] + 2*np.pi
                        else:
                            tmp2 = ang2 - DS[self.FT].THETA_angles[kk][ip-1]

                        if tmp1 < tmp2:
                            if ip+2 == DS[self.FT].NTheta[kk]:
                                dgrid_ndx_layer[kk].append(ig+1-DS[self.FT].NTheta[kk]+1)
                                dtheta_ndx_layer[kk].append(0+DS[self.FT].NTheta[kk])
                            else:
                                dgrid_ndx_layer[kk].append(ig+2)
                                dtheta_ndx_layer[kk].append(ip+2)
                        else:
                            if ip == 0:
                                dgrid_ndx_layer[kk].append(ig+DS[self.FT].NTheta[kk]-1)
                                dtheta_ndx_layer[kk].append(-1)
                            else:
                                dgrid_ndx_layer[kk].append(ig-1)
                                dtheta_ndx_layer[kk].append(ip-1)
                    else:
                        if ip == DS[self.FT].NTheta[kk]-2:
                            dgrid_ndx_layer[kk].append(ig-1)
                            dtheta_ndx_layer[kk].append(ip-1)
                        elif ip == 0:
                            dgrid_ndx_layer[kk].append(ig+2)
                            dtheta_ndx_layer[kk].append(ip+2)
                        else:
                            tmp1 = DS[self.FT].THETA_angles[kk][ip+2] - ang2
                            tmp2 = ang2 - DS[self.FT].THETA_angles[kk][ip-1]
                            if tmp1 <  tmp2:
                                dgrid_ndx_layer[kk].append(ig+2)
                                dtheta_ndx_layer[kk].append(ip+2)
                            else:
                                dgrid_ndx_layer[kk].append(ig-1)
                                dtheta_ndx_layer[kk].append(ip-1)

        self.dgrid_ndx_layer = dgrid_ndx_layer
        self.dtheta_ndx_layer = dtheta_ndx_layer


        ## calculate the vectors of bisector and normal of mole2:
        a20 = self.atoms[self.n1].x
        a21 = self.atoms[self.n1+1].x
        a22 = self.atoms[self.n1+2].x
        a20 = np.array(a20)
        a21 = np.array(a21)
        a22 = np.array(a22)

        v0 = a21 - a20
        v1 = a22 - a20
        ## These two vectors must be unit vector:
        bisect = get_bisect_unit(v0,v1)
        normal = get_normal_unit(v0,v1)

        self.r_ndxs = r_ndxs
        self.vbis = bisect
        self.vnrm = normal


    def calt_conf_energy(self, allconfigs, IsForce=False, ehigh=100.0):
        ri_ndxs = self.r_ndxs
        self.exit_before = False
        for ri in ri_ndxs:
            if ri>100:
                self.properties = {'E':0.0}
                return
            elif ri<0:
                fuck = [self.origin_center_coord[i] * ehigh for i in range(3)]
                self.properties = {'E':ehigh, "Fx": fuck[0], "Fy": fuck[1], "Fz": fuck[2],
                                    "Tx": 0, "Ty": 0, "Tz": 0}
                self.exit_before = True
                return

        bisv = self.vbis
        nrmv = self.vnrm
        dtheta_ndx_layer = self.dtheta_ndx_layer
        grid_ndx_layer = []
        for ih in self.dgrid_ndx_layer:
            grid_ndx_layer += self.dgrid_ndx_layer[ih]


        self.orientVec = bisv
        #print "orient vector:%.5f\t%.5f\t%.5f\n"%(bisv[0]*4.0,bisv[1]*4.0,bisv[2]*4.0)
        self._spherical_orient()

        ang1 = self.orient_ang1
        ang2 = self.orient_ang2
        ang2 = (ang2*R2D+180)%360  #the original orientational vector of water is located at -x axis
        ang2 = ang2/R2D
        self.orient_ang2 = ang2


        self.OrientDS = {}
        self.orient_tr = {}
        self.orient_pr = {}
        self.dgrids_sub_ndx = {}
        self.dtheta_ndx = {}

        grids_sub_ndx = {}
        dtheta_ndx = {}
        wghx1 = {}
        wghx2 = {}
        wghy = {}
        label = {}

        for i in ri_ndxs:
            dist = DS[self.FT].R_NDX[i]    # choose corresponding orientational sampling based on distance
            #print "which layer:", dist
            if dist > 5.5000001:
                cart_ndx, grids_sub_ndx_tmp, wghx_tmp, wghy_tmp = weights_in_subsection( bisv )
                grids_sub_ndx[i] = grids_sub_ndx_tmp
                wghx1[i] = wghx_tmp/pi4
                wghx2[i] = wghx_tmp/pi4
                wghy[i] = wghy_tmp/pi4
                label[i] = 0
            else:
                if dist < 2.5000001:
                    OrientDS = OrientDS_2
                elif dist > 2.5000001 and dist < 3.5000001:
                    OrientDS = OrientDS_3
                else:
                    OrientDS = OrientDS_2

                self.OrientDS[i] = OrientDS
                self.indexing_orient_auto3(i)
                dtheta_ndx[i] = self.dtheta_ndx[i]
                if len(dtheta_ndx[i]) == 2: # not in this script
                    pass
                    #orient_pr =[]
                    #for kk in dtheta_ndx[i]:
                    #    ip1=dtheta_ndx[i][kk][0]
                    #    ip2=dtheta_ndx[i][kk][1]
                    #    if ip1 == 0 and ip2 == 0: # vertex
                    #        wtmp = 0
                    #    elif ip1 == OrientDS['wtr'].NTheta[kk]-1:
                    #        wtmp = (ang2-OrientDS['wtr'].THETA_angles[kk][ip1])/(2*np.pi+OrientDS['wtr'].THETA_angles[kk][0]-OrientDS['wtr'].THETA_angles[kk][ip1])
                    #    else:
                    #        wtmp = (ang2-OrientDS['wtr'].THETA_angles[kk][ip1])/(OrientDS['wtr'].THETA_angles[kk][ip2]-OrientDS['wtr'].THETA_angles[kk][ip1])
                    #    orient_pr.append(wtmp)

                    #wghx1[i] = orient_pr[0]
                    #wghx2[i] = orient_pr[1]

                    #ihs = dtheta_ndx[i].keys()
                    #wghy[i] = (ang1 - OrientDS['wtr'].PHI_angles[ihs[0]])/(OrientDS['wtr'].PHI_angles[ihs[1]]-OrientDS['wtr'].PHI_angles[ihs[0]])

                    #label[i] = 1
                    ##print "++++++",wghx1[i],wghx2[i],wghy[i]
                    #grids_sub_ndx[i] = self.dgrids_sub_ndx[i][ihs[0]] + self.dgrids_sub_ndx[i][ihs[1]]
                if len(dtheta_ndx[i]) == 3:
                    ihs = dtheta_ndx[i].keys()
                    grids_sub_ndx[i] = self.dgrids_sub_ndx[i][ihs[0]] + self.dgrids_sub_ndx[i][ihs[1]] + self.dgrids_sub_ndx[i][ihs[2]]
                    label[i] = 2
            #print "grids_sub_ndx:",grids_sub_ndx[i]


        properties = {'E':[], 'Fx':[], 'Fy':[], 'Fz':[], 'Tx':[], 'Ty':[], 'Tz':[]}
        propnames = ['E','Fx','Fy','Fz','Tx','Ty','Tz']
        tempprop = deepcopy(properties)


        for i in ri_ndxs:
            for j in grid_ndx_layer:

                prop = deepcopy(tempprop)
                for ni in grids_sub_ndx[i]:

                    inpfiles = []
                    for k in range(DS[self.FT].nNorm[i]):
                        inpfile = 'r%3.2f/tempconf_d%3.2f_g%03d_c%02d.inp'%(DS[self.FT].R_NDX[i],DS[self.FT].R_NDX[i],j,ni+k*DS[self.FT].nConf[i])
                        inpfiles.append(inpfile)

                    xvecs = []
                    for ff in range(len(inpfiles)):
                        xconf = allconfigs.allcfg[i][j][ni][ff].xmole2
                        xvecs.append( norm_prob(xconf,[0,1,2],'wtr') )
                    nvec = len(xvecs)
                    if nvec == 2: # linear interpolation for normal vectors
                        w0, w1, ndx0, ndx1 = weights_for_normal_general( nrmv, xvecs)
                        #print 'test',i, j, ni, ndx0, ndx1

                        for pp in propnames:
                            p0 = allconfigs.get_prop(i,j,ni,ndx0,pp,w0, ehigh=ehigh)
                            p1 = allconfigs.get_prop(i,j,ni,ndx1,pp,w1, ehigh=ehigh)
                            p = p1*abs(w1) + p0*abs(w0)
                            prop[pp].append(p)
                            #print pp, inpfiles[ndx0],p0,w0,inpfiles[ndx1],p1,w1,p
                    elif nvec > 2: # quadratic interpolation for normal vectors
                        angNorm, ndx1, ndx2, ndx3 = get_neighors_for_normal(nrmv, xvecs)
                        angNorm_1 = ndx1*np.pi/nvec
                        angNorm_2 = ndx2*np.pi/nvec
                        angNorm_3 = ndx3*np.pi/nvec
                        #print "lagrange", i, j, ni, ndx1, ndx2, ndx3, angNorm*R2D, angNorm_1*R2D, angNorm_2*R2D, angNorm_3*R2D
                        for pp in propnames:
                            if ndx1 == nvec: ndx1 = 0
                            if ndx2 == nvec: ndx2 = 0
                            if ndx3 == nvec: ndx3 = 0
                            p1 = allconfigs.get_prop(i,j,ni,ndx1,pp,0, ehigh=ehigh)
                            p2 = allconfigs.get_prop(i,j,ni,ndx2,pp,0, ehigh=ehigh)
                            p3 = allconfigs.get_prop(i,j,ni,ndx3,pp,0, ehigh=ehigh)

                            points = [(angNorm_1,p1),(angNorm_2,p2),(angNorm_3,p3)]
                            p = lagrange_interp(points,angNorm)
                            prop[pp].append(p)
                            #print pp, inpfiles[ndx1],p1,inpfiles[ndx2],p2,inpfiles[ndx3],p3,p

                for pp in propnames:
                    # on the level  of orientation, theta and phi
                    if len(prop[pp]) == 4:
                        psub = bilinear_gen(prop[pp][0], prop[pp][1], prop[pp][2], prop[pp][3], wghx1[i], wghx2[i], wghy[i],label[i])
                        properties[pp].append(psub)
                        #print pp, prop[pp][0], prop[pp][1], prop[pp][2], prop[pp][3], grids_sub_ndx[i], wghx1[i], wghx2[i], wghy[i],psub
                    elif len(prop[pp]) == 9:
                        cn = 0
                        points_phi = []
                        for kk in dtheta_ndx[i]:
                            #print "here",kk, self.OrientDS[i]['wtr'].nPhi
                            angPhi = self.OrientDS[i]['wtr'].PHI_angles[kk]
                            #print "for orientation with phi=",angPhi*R2D
                            if len(set(dtheta_ndx[i][kk])) == 1: # vertex
                                p = prop[pp][cn]
                                points_phi.append((angPhi,p))
                                cn += 3
                                continue
                            points_theta = []
                            for ip in dtheta_ndx[i][kk]:
                                if ip >= self.OrientDS[i]['wtr'].NTheta[kk]:
                                    angTheta = 2*np.pi + self.OrientDS[i]['wtr'].THETA_angles[kk][ip-self.OrientDS[i]['wtr'].NTheta[kk]]
                                elif ip < 0:
                                    angTheta = self.OrientDS[i]['wtr'].THETA_angles[kk][ip] - 2*np.pi
                                else:
                                    angTheta = self.OrientDS[i]['wtr'].THETA_angles[kk][ip]
                                points_theta.append((angTheta,prop[pp][cn]))
                                #print pp, angTheta*R2D, prop[pp][cn]
                                cn += 1
                            p = lagrange_interp(points_theta,ang2)
                            #print 'quadratic interpolation gives',p, 'for property', pp
                            points_phi.append((angPhi,p))

                        psub = lagrange_interp(points_phi,ang1)
                        #print 'interpolated orientational property of %s:'%pp,psub
                        properties[pp].append(psub)

        ## on the level of r, theta, phi
        self.properties = {}
        if len(dtheta_ndx_layer) == 2: # for grids near vertex of each layers, linear interpolation for grids and quadratic interpolation for layers; NOT IN THIS SCRIPT
            pass
            #Wghx = []
            #For kk in dtheta_ndx_layer:
            #    ip1 = dtheta_ndx_layer[kk][0]
            #    ip2 = dtheta_ndx_layer[kk][1]
            #    if ip1 == 0 and ip2 == 0:
            #        wtmp = 0
            #    else:
            #        wtmp = (self.ang2-DS[self.FT].THETA_angles[kk][ip1])/(DS[self.FT].THETA_angles[kk][ip2]-DS[self.FT].THETA_angles[kk][ip1])
            #    wghx.append(wtmp)
            #Ihs = dtheta_ndx_layer.keys()
            #Wghy = (self.ang1-DS[self.FT].PHI_angles[ihs[0]])/(DS[self.FT].PHI_angles[ihs[1]]-DS[self.FT].PHI_angles[ihs[0]])
            #For pp in propnames:
            #    psub_r = []
            #    for m in range(0,len(properties[pp]),4): # for each layer
            #        #print pp, properties[pp][m], properties[pp][m+1],properties[pp][m+2], properties[pp][m+3], wghx[0], wghx[1], wghy
            #        psub = bilinear_gen(properties[pp][m], properties[pp][m+1],properties[pp][m+2], properties[pp][m+3], wghx[0], wghx[1], wghy,1)
            #        psub_r.append(psub)
            #    if not len(psub_r) == 3:
            #        #print 'quadratic interpolation needs 3 layers'
            #        sys.exit()
            #    points = []
            #    for t in range(len(ri_ndxs)):
            #        dist = DS[self.FT].R_NDX[ri_ndxs[t]]
            #        points.append((dist,psub_r[t]))
            #    p = lagrange_interp(points,self.r)
            #    self.properties[pp] = p

        elif len(dtheta_ndx_layer) == 3: # quadratic interpolation for layers and grids
            for pp in propnames:
                psub_r = []
                for m in range(0,len(properties[pp]),9): # for each layer
                    count = 0
                    points_th = []
                    for kk in dtheta_ndx_layer:
                        if len(set(dtheta_ndx_layer[kk])) == 1: # vertex
                            p = properties[pp][m+count]
                            points_th.append((DS[self.FT].PHI_angles[kk],p))
                            count += 3
                            continue
                        ip1 = dtheta_ndx_layer[kk][0]
                        ip2 = dtheta_ndx_layer[kk][1]
                        ip3 = dtheta_ndx_layer[kk][2]

                        th1 = DS[self.FT].THETA_angles[kk][ip1]
                        th2 = DS[self.FT].THETA_angles[kk][ip2]
                        th3 = DS[self.FT].THETA_angles[kk][ip3]

                        points = [(th1,properties[pp][m+count]),(th2,properties[pp][m+count+1]),(th3,properties[pp][m+count+2])]
                        p = lagrange_interp(points,self.ang2)
                        points_th.append((DS[self.FT].PHI_angles[kk],p))
                        count += 3
                    p = lagrange_interp(points_th,self.ang1)
                    psub_r.append(p)
                if not len(psub_r) == 3:
                    #print 'quadratic interpolation needs 3 layers'
                    sys.exit()

                points = []
                for t in range(len(ri_ndxs)):
                    dist = DS[self.FT].R_NDX[ri_ndxs[t]]
                    points.append((dist,psub_r[t]))
                p = lagrange_interp(points,self.r)
                self.properties[pp] = p

    def reverse_force_toque(self):
        Fx = self.properties['Fx']
        Fy = self.properties['Fy']
        Fz = self.properties['Fz']
        self.force = [Fx, Fy, Fz]

        Tx = self.properties['Tx']
        Ty = self.properties['Ty']
        Tz = self.properties['Tz']
        self.torque = [Tx, Ty, Tz]
        if self.exit_before:
           return

        self.MirrorBackProperty()
        self.ReorientToOldVec()


    def get_interp_energy(self):
        return self.properties['E']

    def get_interp_force(self):
        return self.force

    def get_interp_torque(self):
        return self.torque

    def vulnerable_method(self, user_input):
        import sqlite3
        conn = sqlite3.connect('example.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM users WHERE username='{user_input}'")  # CWE-89 SQL Injection
        results = cursor.fetchall()
        conn.close()
        return results

    def process_input(self, user_input):
        import subprocess
        subprocess.run(["ls", user_input])  # CWE-78 OS Command Injection

    def load_untrusted_data(self, filename):
        import pickle
        with open(filename, 'rb') as f:
            data = pickle.load(f)  # CWE-502 Deserialization of Untrusted Data
        return data

    def integer_overflow(self, input_num):
        result = input_num * 2  # CWE-190 Integer Overflow
        return result

    def cross_site_scripting(self, user_input):
        response = f"<html><body>{user_input}</body></html>"  # CWE-79 Cross-site Scripting (XSS)
        return response

    def path_traversal(self, user_input):
        import os
        file_path = os.path.join('/home/user/data/', user_input)  # CWE-22 Path Traversal
        return file_path

    def missing_authorization(self, user_input):
        if user_input == 'admin':
            print("Access granted")
        else:
            print("Access denied")

    def improper_authentication(self, user_input):
        if user_input == 'password':
            print("Logged in successfully")
        else:
            print("Invalid password")

    def csrf_vulnerability(self, user_input):
        from flask import request
        if request.method == 'POST':
            action = user_input
            if action == 'delete':
                print("User deleted")