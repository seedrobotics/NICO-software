import datetime
import logging
import os
import time

import cv2

from ImageWriter import ImageWriter
from VideoDevice import VideoDevice


def get_devices():
    """
    Returns a list containing the possible path of all video capturing devices

    :return: Video devices
    :rtype: list
    """
    return VideoDevice.get_all_devices()


class ImageRecorder:
    """
    The ImageRecorder class enables the capturing of images from a camera.
    """

    def __init__(self, device='', width=640, height=480, framerate=20,
                 zoom=None, pan=None, tilt=None, settings_file=None,
                 setting="standard", writer_threads=2, compressed=True,
                 pixel_format="MJPG", calibration_file=None):
        """
        Initialises the ImageRecorder with a given device.

        The device must be contained in :meth:`get_devices`

        :param device: Device name
        :type device: str
        :param width: Width of image
        :type width: float
        :param height: Height of image
        :type height: float
        :param framerate: number of frames per second
        :type framerate: int
        :param value: zoom value between 100 and 800 (overwrites settings)
        :type value: int
        :param value: pan value between -648000 and 648000, step 3600
        (overwrites settings)
        :type value: int
        :param value: tilt value between -648000 and 648000, step 3600
        (overwrites settings)
        :type value: int
        :param file_path: the settings file
        :type file_path: str
        :param setting: name of the setting that should be applied
        :type setting: str
        :param writer_threads: Number of worker threads for image writer
        :type writer_threads: int
        :param pixel_format: fourcc codec
        :type pixel_format: string
        """
        self._device = VideoDevice.from_device(device, framerate, width,
                                               height, zoom, pan, tilt,
                                               settings_file, setting,
                                               compressed, pixel_format,
                                               calibration_file)
        if self._device is None:
            logging.error('Can not create device from path' +
                          str(self._device))
        self._target = 'picture-{}.png'
        self._image_writer = ImageWriter(writer_threads)

    def load_settings(self, file_path, setting="standard"):
        """
        Loads a settings json file and applies the given setting to all cameras

        :param file_path: the settings file
        :type file_path: str
        :param setting: name of the setting that should be applied
        :type setting: str
        """
        self._device.load_settings(file_path, setting)

    def camera_value(self, value_name, value):
        """
        Sets zoom value if camera supports it. Requires v4l-utils.

        :param value: zoom value between 100 and 800
        :type value: int
        """
        self._device.camera_value(value_name, value)

    def zoom(self, value):
        """
        Sets zoom value if camera supports it. Requires v4l-utils.

        :param value: zoom value between 100 and 800
        :type value: int
        """
        self._device.zoom(value)

    def enable_write(self, state=True):
        """
        Sets the writing to disk state

        :param state: Write enabled
        :type value: bool
        """
        self._image_writer.enable_write(state)

    def pan(self, value):
        """
        Sets pan (x-axis) value if camera supports it. Requires v4l-utils.

        :param value: pan value between -648000 and 648000, step 3600
        :type value: int
        """
        self._device.pan(value)

    def tilt(self, value):
        """
        Sets tilt (y-axis) value if camera supports it. Requires v4l-utils.

        :param value: tilt value between -648000 and 648000, step 3600
        :type value: int
        """
        self._device.tilt(value)

    def save_one_image(self):
        """
        Saves an image to a unique file

        :return: Path (or '' if an error occured
        :rtype: str
        """
        path = 'picture-' + datetime.datetime.today().isoformat() + '.png'
        return os.path.abspath(path) if self.save_image_to(path) else ''

    def save_image_to(self, path):
        """
        Saves an Image to a given file

        :param path: Target file
        :return: True if successful
        :rtype: bool
        """
        self._target = path
        if self._device is None:
            logging.error('Capture device not initialized')
            return False
        if not self._device._open:
            self._device.open()
        self._device.add_callback(self._callback)
        time.sleep(.1)
        self._device.close()
        self._device.clean_callbacks()
        return True

    def start_recording(self, path="picture-{}.png"):
        self._target = path
        if not self._device._open:
            self._device.open()
        if not self._image_writer._open:
            self._image_writer.open()
        self._device.add_callback(self._callback)

    def stop_recording(self, wait_for_writer=True):
        """
        Saves an Image to a given file

        :param wait_for_writer: Whether execution should be blocked until all
                                images are written (WARNING if this is set to
                                False wait_for_writer() needs to be called
                                to avoid memory leaks)
        :type wait_for_writer: bool
        """
        self._device.close()
        self._device.clean_callbacks()
        if wait_for_writer:
            self.wait_for_writer()

    def wait_for_writer(self):
        self._image_writer.close()

    def custom_callback(self, iso_time, frame):
        # Option to create a custom function, that modifies the frame before
        # saving
        return frame

    def _callback(self, rval, frame):
        """
        Internal callback

        :param rval: rval
        :param frame: frame
        """
        if rval:
            iso_time = datetime.datetime.today().isoformat()

            frame = self.custom_callback(
                iso_time, frame)

            self._image_writer.write_image(self._target.format(
                iso_time), frame)
