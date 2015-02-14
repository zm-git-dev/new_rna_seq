import logging
logging.disable(logging.CRITICAL)


import unittest
import mock
import sys
import os
import StringIO
import __builtin__

# for finding modules in the sibling directories
from os import path
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

from utils.util_classes import Params
from utils.pipeline import Pipeline
from utils.project import Project
from utils.custom_exceptions import *
import utils.config_parser
from utils.util_methods import *


def dummy_join(a,b):
	return os.path.join(a,b)


class TestParams(unittest.TestCase):
	"""
	Tests the Params object.		
	"""

	def test_add_key_value_pair(self):
		p = Params()
		v = "some_value"
		p.add( key = v)
		self.assertEqual(p.get("key"), v)

	def test_add_multiple_key_value_pairs(self):
		p = Params()
		v1 = "some_value"
		v2 = "other_value"
		p.add( key1 = v1, key2 = v2)
		self.assertEqual(p.get("key1"), v1)
		self.assertEqual(p.get("key2"), v2)

	def test_add_dict(self):
		p = Params()
		d = {"a":1, "b":2}
		p.add(d)
		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)

	def test_add_multiple_dicts(self):
		p = Params()
		d1 = {"a":1, "b":2}
		d2 = {"c":3, "d":4}
		p.add(d1, d2)
		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)
		self.assertEqual(p.get("c"), 3)
		self.assertEqual(p.get("d"), 4)

	def test_add_both_simultaneously(self):
		p = Params()
		v = "some_value"
		d = {"a":1, "b":2}

		p.add(d, key = v)

		self.assertEqual(p.get("a"), 1)
		self.assertEqual(p.get("b"), 2)
		self.assertEqual(p.get("key"), v)

	def test_asking_for_missing_value_kills_pipeline(self):
		p = Params()

		# add some value. Not necessary to do this.
		v = "some_value"
		p.add( key = v)
		self.assertRaises(ParameterNotFoundException, p.get, "missing_val")

	def test_reset_param(self):
		p = Params()
		v = "some_value"
		p.add( key = v)
		p.reset_param('key', 'new_value')
		self.assertEqual(p.get('key'), 'new_value')


	def test_trying_to_reset_unset_param_raises_exception(self):
		with self.assertRaises(ParameterNotFoundException):
			p = Params()
			p.reset_param('key', 'new_value')


class TestProject(unittest.TestCase):
	"""
	Tests the Project object
	"""
	@mock.patch('utils.util_methods.os')
	def test_missing_default_config_file_with_no_alternative_given(self, mock_os):
		"""
		No config file passed via commandline and none found in the project_configuration directory
		"""
		
		# mock the missing config file: 
		mock_os.listdir.return_value = []

		# mock there being no command line arg passed for a different config file:
		mock_cl_args = {'project_configuration_file': None}
		
		# mock the pipeline params
		mock_pipeline_params = {'project_configurations_dir': '/path/to/proj_config_dir'}

		with self.assertRaises(ConfigFileNotFoundException):
			p = Project(mock_cl_args)
			p.prepare(mock_pipeline_params)


	@mock.patch('utils.util_methods.os')
	def test_missing_alternative_config_file(self, mock_os):
		"""
		Config filepath passed via commandline, but is not found.
		"""
		
		# mock a default config file (doesn't matter since the alternative takes precedent): 
		mock_os.listdir.return_value = []

		# mock there being a command line arg passed for a different config file:
		mock_cl_args = {'project_configuration_file': 'alternate.cfg'}

		# mock the pipeline params
		mock_pipeline_params = {'project_configurations_dir': '/path/to/proj_config_dir'}

		# here we mock the open() builtin method.  Without this, one could conceivably have
		# the above (intended fake) file in their filesystem, which would cause the test to fail (since said file
		# is, in fact, present).  If the file is not present, open() raises IOError.
		with mock.patch.object(__builtin__, 'open', mock.mock_open()) as mo:
			mo.side_effect = IOError
			with self.assertRaises(ConfigFileNotFoundException):
				p = Project(mock_cl_args)
				p.prepare(mock_pipeline_params)


	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.util_methods.os')
	def test_multiple_config_file_with_no_alternative_given(self, mock_os, mock_join):
		"""
		No config file passed via commandline and multiple found in the project_configurations directory
		"""
		
		# mock the multiple config files: 
		mock_os.listdir.return_value = ['a.cfg','b.cfg']

		# mock there being no command line arg passed for a different config file:
		mock_cl_args = {'project_configuration_file': None}

		# mock the pipeline params
		mock_pipeline_params = {'project_configurations_dir': '/path/to/proj_config_dir'}

		with self.assertRaises(MultipleConfigFileFoundException):
			p = Project(mock_cl_args)
			p.prepare(mock_pipeline_params)


	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.config_parser.read')
	@mock.patch('utils.util_methods.os')
	def test_parses_alternative_config_file(self, mock_os, mock_cfg_reader, mock_join):
		"""
		Assumptions-- os.listdir() finds a single .cfg file in the pipeline home directory.
		A custom config file passed via commandline.
		"""
		
		# mock the missing config file: 
		mock_os.listdir.return_value = ['default.cfg']

		# mock there being no command line arg passed for a different config file:
		custom_cfg_filepath = '/path/to/custom.cfg'
		mock_cl_args = {'project_configuration_file': custom_cfg_filepath}

		# mock the pipeline params
		mock_pipeline_params = {'project_configurations_dir': '/path/to/proj_cfg_dir'}

		# mock the return from the reader
		mock_cfg_dict = {'a':1, 'b':2}
		mock_cfg_reader.return_value = mock_cfg_dict

		with mock.patch.object(__builtin__, 'open', mock.mock_open()) as mo:
			p = Project(mock_cl_args)			
			p.prepare(mock_pipeline_params)

		# the expected parameters
		expected_param_dict = {'project_configuration_file': custom_cfg_filepath}
		expected_param_dict.update(mock_cfg_dict)

		self.assertEqual(p.project_params.get_param_dict(), expected_param_dict)


class TestPipeline(unittest.TestCase):
	"""
	Tests the Pipeline object
	"""

	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.config_parser.read')
	@mock.patch('utils.util_methods.os')
	def test_missing_default_pipeline_config_file(self, mock_os, mock_cfg_reader, mock_join):
		"""
		Assumptions-- os.listdir() finds a single .cfg file in the pipeline home directory.
		No config file passed via commandline.
		"""
		
		default_cfg_name = 'default.cfg'

		# mock the default config file NOT being found in the home dir: 
		mock_os.listdir.return_value = []

		# create a Pipeline object, which will be populated with the mock return dictionary
		dummy_path = "path/to/home"

		with self.assertRaises(ConfigFileNotFoundException):
			p = Pipeline(dummy_path)
			p.setup()



	@mock.patch('utils.util_methods.os.path.join', side_effect=dummy_join)
	@mock.patch('utils.config_parser.read')
	@mock.patch('utils.util_methods.os')
	def test_raises_exception_if_missing_pipeline_components(self, mock_os, mock_cfg_reader, mock_join):
		"""
		This covers where the genome or component directories could be missing (or the path to them is just wrong)
		"""
		
		default_cfg_name = 'default.cfg'

		# mock the default config file being found in the home dir: 
		mock_os.listdir.return_value = [default_cfg_name]
		mock_os.path.isfile.return_value = True

		# mock the return from the reader- does not matter if this is a complete list of the actual, current pipeline components/pieces--
		mock_cfg_dict = {'components_dir':'components', 'genomes_dir':'genome_info'}
		mock_cfg_reader.return_value = mock_cfg_dict

		# create a Pipeline object, which will be populated with the mock return dictionary
		dummy_path = "/path/to/pipeline_home"

		with mock.patch.object(__builtin__, 'open', mock.mock_open()) as mo:
			p = Pipeline(dummy_path)
			mock_os.path.isdir.return_value = False # this mocks the directory not being found
			with self.assertRaises(MissingComponentDirectoryException):
				# this ensures that the method looking for the directory returns a false.  Otherwise it is possible to pass
				# a 'correct' mock parameter (i.e. a directory that actually does exist) which would cause the test to fail
				mock_os.path.isdir.return_value = False   
				p.setup()



class TestConfigParser(unittest.TestCase):

	def test_parser_correctly_parses_comma_list(self):
		'''
		The config files can contain comma-separated values-- ensure that the key gets mapped to a list composed of those comma-separated vals
		'''

		# sample text from a config file		
		cfg_text = "[dummy_section] \na = 1 \nb = x, y, z"
		
		# expected dictionary result:
		expected_result = {'a':'1', 'b':['x','y','z']}

		#create a fake config file-like object using StringIO
		fake_file = StringIO.StringIO()
		fake_file.write(cfg_text)
		fake_file.seek(0)

		result = utils.config_parser.read(fake_file)
		self.assertEqual(result, expected_result)









if __name__ == "__main__":
	unittest.main()
