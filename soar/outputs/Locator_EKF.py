#__author__ = 'Mohammadreza'
import numpy as np
from math import pi
from time import *

class Locator_EKF:
    def __init__(self, pos, heading, wheel_distance = 0.1):
        self.l = wheel_distance
        self.R = np.asmatrix( np.diag(np.array([1,1,1])) ) # The measurment covariance matrix
        self.Q = np.asmatrix( 0.01*np.identity(5) ) # Process covariance matrix
        self.H = np.matrix([[0, 0, 1, 0, 0],
                            [0, 0, 0, 1, 0],
                            [0, 0, 0, 0, 1]])
        self.P = np.asmatrix( np.identity(5) ) # Initial covariance matrix
        self.x = np.matrix( [ [pos[0]] , [pos[1]] , [heading], [0.] , [0.] ])
        return

    def get_position(self):
        return self.x[0,0] , self.x[1,0]
    
    def get_heading(self):
        return self.x[2,0]

    def update_state(self,data,Ts):
        """
        :param x: x is the latest position and heading of the robot.
            It has to be in the form of a vector i.e. 5 by 1 matrix
        :param P: the latest value of the covariance matrix
        :param data: the measurement vector: 3 by 1 matrix which includes the rotational
            velocity from Gyro, and right and left motor speeds from encoder
        :param Ts: the sampling time
        :return: it returns updated x which is a vector of updated
        position and heading (x,y,theta) and the covariance matrix
        """
        t1 = time()
        z = np.matrix([ [data[0]] , [data[1]] , [data[2]] ])
        x1 = np.array([[self.x[0] + Ts/2*(self.x[3]+self.x[4])*np.cos(self.x[2])],# Updates state
                       [self.x[1] + Ts/2*(self.x[3]+self.x[4])*np.sin(self.x[2])],
                       [self.x[2] + Ts/self.l*(self.x[3]-self.x[4])],
                       [self.x[3]],
                       [self.x[4]]])
        x1 = np.asmatrix(x1)
        x1 = np.transpose(x1)
        A = np.matrix([[1, 0, -Ts/2*(x1[3]+x1[4])*np.sin(x1[2]),  Ts/2*np.cos(x1[2]),  Ts/2*np.cos(x1[2])], # Jacoobian
                       [0, 1,  Ts/2*(x1[3]+x1[4])*np.cos(x1[2]),  Ts/2*np.sin(x1[2]),  Ts/2*np.sin(x1[2])],
                       #[0, 0,  1,                                                0,                        0],
                       [0, 0,  1,                                                Ts/self.l,               -Ts/self.l],
                       [0, 0,  0,                                                1,                        0],
                       [0, 0,  0,                                                0,                        1]])
        self.P = A*self.P*A.T+self.Q
        z1 = np.array([[x1[2]],
                       [x1[3]],
                       [x1[4]]])
        z1 = np.asmatrix(z1)
        z1 = z1.T
        P12 = self.P*self.H.T

        R = np.linalg.cholesky(self.H*P12+self.R)
        U = P12*np.linalg.inv(R)
        self.x = x1 + U *( R.T.I*(z-z1) )
        self.P = self.P-U*U.T
        #if self.x[0,0]>pi:
        #    self.x[0,0]-=2*pi
        #elif self.x[0,0]<-pi:
        #    self.x[0,0]+=2*pi
        #print time()-t1,self.x[2,0]
        return self.x[0,0] , self.x[1,0] , self.x[2,0] 
