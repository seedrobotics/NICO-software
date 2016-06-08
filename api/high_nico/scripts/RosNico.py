#!/usr/bin/env python

# Copyright (C) 2016 Marcus Soll
#
# This file is part of highNICO.
#
# highNICO is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# highNICO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with highNICO. If not, see <http://www.gnu.org/licenses/>.

from HighNico import HighNico
import logging
import argparse
import sys

import rospy
from high_nico.msg import s, sif, i, empty

class RosNico():
    """
    The RosNico class exposes the functions of HighNico to ROS
    """

    @staticmethod
    def getConfig():
        """
        Returns a default config dict
        :return: dict
        """
        return {'logFile': 'NICO.log',
                'robotMotorFile': 'config.json',
                'vrep': False,
                'vrepHost': '127.0.0.1',
                'vrepPort': 19997,
                'vrepScene': None,
                'rostopicName': '/nico'
                }

    def __init__(self, config = None):
        """
        RosNico provides HighNico functions over ROS
        :param config: Configuration of the HighNico and RosNico interface
        :type config: dict
        """
        self.robot = None
        if config is None:
            config = RosNico.getConfig()

        # init highNICO
        logging.info('-- Init rosNICO --')
        self.robot = HighNico(motorConfig=config['robotMotorFile'], vrep=config['vrep'], vrepHost=config['vrepHost'], vrepPort=config['vrepPort'], vrepScene=config['vrepScene'])

        # init ROS
        logging.debug('Init ROS')
        rospy.init_node('ros_nico', anonymous=True)

        # setup subscriber
        logging.debug('Init subscriber')
        rospy.Subscriber('%s/openHand' % config['rostopicName'], s, self._ROSPY_openHand)
        rospy.Subscriber('%s/closeHand' % config['rostopicName'], s, self._ROSPY_closeHand)
        rospy.Subscriber('%s/openHandParam' % config['rostopicName'], sif, self._ROSPY_openHandParam)
        rospy.Subscriber('%s/closeHandParam' % config['rostopicName'], sif, self._ROSPY_closeHandParam)
        rospy.Subscriber('%s/enableForceControl' % config['rostopicName'], i, self._ROSPY_enableForceControl)
        rospy.Subscriber('%s/disableForceControl' % config['rostopicName'], empty, self._ROSPY_disableForceControl)

        # wait for messages
        logging.info('-- All done --')

    def _ROSPY_openHand(self, message):
        """
        Callback handle for openHand
        :param message: ROS message
        :type message: high_nico.msg.string
        :return: None
        """
        self.robot.openHand(message.param1)

    def _ROSPY_closeHand(self, message):
        """
        Callback handle for closeHand
        :param message: ROS message
        :type message: high_nico.msg.s
        :return: None
        """
        self.robot.closeHand(message.param1)

    def _ROSPY_openHandParam(self, message):
        """
        Callback handle for openHand with additional parameters
        :param message: ROS message
        :type message: high_nico.msg.sif
        :return: None
        """
        self.robot.openHand(message.param1, message.param2, message.param3)

    def _ROSPY_closeHandParam(self, message):
        """
        Callback handle for closeHand with additional parameters
        :param message: ROS message
        :type message: high_nico.msg.sif
        :return: None
        """
        self.robot.closeHand(message.param1, message.param2, message.param3)

    def _ROSPY_enableForceControl(self, message):
        """
        Callback handle for enableForceControl
        :param message: ROS message
        :type message: high_nico.msg.i
        :return: None
        """
        self.robot.enableForceControl(message.param1)

    def _ROSPY_disableForceControl(self, message):
        """
        Callback handle for disableForceControl
        :param message: ROS message
        :type message: high_nico.msg.empty
        :return: None
        """
        self.robot.disableForceControl()

    def __del__(self):
        self.robot.cleanup()

if __name__ == '__main__':
    config = RosNico.getConfig()

    # Parse command line
    parser = argparse.ArgumentParser(description='NICO ROS interface')
    parser.add_argument('--log-level', dest='logLevel', help='Sets log level. Default: INFO', type=str)
    parser.add_argument('--log-file', dest='logFile', help='Path to log file. Default: %s' % config['logFile'], type=str)
    parser.add_argument('-m', '--motor-file', dest='robotMotorFile', help='Path to robot motor file. Default: %s' % config['robotMotorFile'], type=str)
    parser.add_argument('-v', '--vrep', dest='vrep', help='Connect to VREP rather than to a real robot', action='store_true')
    parser.add_argument('--vrep-host', dest='vrepHost', help='Host of VREP. Default: %s' % config['vrepHost'], type=str)
    parser.add_argument('--vrep-port', dest='vrepPort', help='Port of VREP. Default: %i' % config['vrepPort'], type=int)
    parser.add_argument('--vrep-scene', dest='vrepScene', help='Scene to load in VREP. Default: %s' % config['vrepScene'], type=str)
    parser.add_argument('--rostopic-name', dest='rostopicName', help='Topic name for ROS. Default: %s' % config['rostopicName'], type=str)

    args = parser.parse_known_args()[0]
    if args.logFile:
        config['logFile'] = args.logFile
    if args.robotMotorFile:
        config['robotMotorFile'] = args.robotMotorFile
    config['vrep'] = args.vrep
    if args.vrepHost:
        config['vrepHost'] = args.vrepHost
    if args.vrepPort:
        config['vrepPort'] = args.vrepPort
    if args.vrepScene:
        config['vrepScene'] = args.vrepScene
    if args.rostopicName:
        config['rostopicName'] = args.rostopicName

    # Set logging setting
    loggingLevel = logging.INFO
    try:
        loggingLevel = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'CRITICAL': logging.CRITICAL,
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'critical': logging.CRITICAL,
        }[args.logLevel]
    except:
        sys.stderr.write('LOGGING ERROR: Unknown log level %s\n' % args.logLevel)
        pass

    logging.basicConfig(filename=config['logFile'],
                        format='%(asctime)s %(levelname)s at %(funcName)s (%(module)s: %(lineno)d): %(message)s',
                        level=loggingLevel)
    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(loggingLevel)
    logging_format = logging.Formatter(
        '%(asctime)s %(levelname)s at %(funcName)s (%(module)s: %(lineno)d): %(message)s')
    stdoutHandler.setFormatter(logging_format)
    logging.getLogger().addHandler(stdoutHandler)

    rosConnection = RosNico(config)

    rospy.spin()