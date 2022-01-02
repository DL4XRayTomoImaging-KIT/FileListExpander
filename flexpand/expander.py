from glob import glob
import re
import os
import yaml


class MetaArger:
    def __init__(self, verbosity=False, args_prefix='', list_file_extension='txt') -> None:
        self.v = verbosity
        self.lfe = list_file_extension
        self.ap = args_prefix

    def _log(self, m):
        if self.v:
            print(m)
    
    def _get_arg_name(self, name):
        if self.ap is None:
            return name
        else:
            return f'{self.ap}-{name}'
    
    def _add_config_to_args(self, parser):
        parser.add_argument(self._get_arg_name('config'), help='YAML file containing dictionary of values for all parameters (name without leading dashes).')
        self.args[self._get_arg_name('config')] = 'config'
    
    def _unpack_args(self, args):
        unpacked = {}
        for arg_name in self.args:
            unpacked[arg_name] = getattr(args, self._get_arg_name(arg_name))
        return unpacked
    
    def _unpack_params(self, params):
        unpacked = {}
        for arg_name in self.args:
            if arg_name in params.keys():
                unpacked[arg_name] = params[arg_name]
            elif self._get_arg_name(arg_name) in params.keys():
                unpacked[arg_name] = params[self._get_arg_name(arg_name)]
        return unpacked
    
def _unpack_cmd(call):
    def wrapped_call(self, *args, **kwargs):
        if 'args' in kwargs.keys():
            kwargs.update(self._unpack_args(kwargs.pop('args')))
            return call(self, *args, **kwargs)
        else:
            return call(self, *args, **kwargs)
    
    return wrapped_call

def _unpack_yaml(call):
    def wrapped_call(self, *args, **kwargs):
        if 'config' in kwargs.keys():
            with open(kwargs.pop('config')) as f:
                config = yaml.safe_load(f)
            kwargs.update(config)
            return call(self, *args, **kwargs)
        else:
            return call(self, *args, **kwargs)
    
    return wrapped_call


class Expander(MetaArger):
    def __init__(self, list_file_extension='txt', verbosity=False, files_only=True, args_prefix='input'):
        self.lfe = list_file_extension
        self.fo = files_only
        self.ap = args_prefix

        super().__init__(verbosity=verbosity, args_prefix=args_prefix, list_file_extension=list_file_extension)

    def _process_one_file(self, one_addr):
        if os.path.exists(one_addr):
            if self.fo:
                if os.path.isfile(one_addr):
                    self._log(f'adding path "{one_addr}" to queue.')
                    return one_addr
                else:
                    self._log(f'path "{one_addr}" is not a file.')
                    return None
            else:
                self._log(f'adding path "{one_addr}" to queue.')
                return one_addr
        else:
            self._log(f'path "{one_addr}" does not exist.')
            return None

    def _process_files_list(self, addresses):
        proper_addresses = []
        for one_addr in addresses:
            processed_addr = self._process_one_file(one_addr)
            if processed_addr is not None:
                proper_addresses.append(processed_addr)

        return proper_addresses

    def _process_list_file(self, main_addr):
        with open(main_addr) as f:
            addresses = f.read().split('\n')
        addresses = [one_addr for one_addr in addresses if not one_addr.startswith('#')] # removing commented lines
        addresses = [one_addr.split(' #')[0].strip() for one_addr in addresses] # removing comments and star/end spaces

        addr_list = self._process_files_list(addresses)
        return addr_list

    def _process_directory(self, main_addr):
        all_content = glob(os.path.join(main_addr, '*'))
        return self._process_files_list(all_content)

    def _process_glob(self, main_addr):
        all_content = glob(main_addr)
        return self._process_files_list(all_content)

    def _filter_with_regexp(self, addresses, regexp, regexp_option):
        if regexp is None:
            return addresses # nothing to do here. Woooosh!

        compiled = re.compile(regexp)
        filtered = []
        for addr in addresses:
            if (regexp_option == 'contains') and compiled.findall(addr):
                filtered.append(addr)
            elif (regexp_option == 'matches') and (compiled.match(addr) is not None):
                filtered.append(addr)
            elif (regexp_option == 'not_contains') and not compiled.findall(addr):
                filtered.append(addr)
            elif (regexp_option == 'not_matches')and (compiled.match(addr) is None):
                filtered.append(addr)
            else:
                self._log(f'path {addr} removed while filtering with regular expression')

        return filtered

    def add_args(self, parser):
        parser.add_argument('--'+self._get_arg_name('files'), 
                            help=f'''Files to work with.
                            It could be either file list (only works with YAML configuration file), directory containing files to be processed, wildcarded path, or .{self.lfe} file containing one file address per line''')
        parser.add_argument('--'+self._get_arg_name('regexp'), default=None, help=f'RegExp to filter files obtained from {self._get_arg_name("files")} argument. Should be standard python-style regular expression.')
        parser.add_argument('--'+self._get_arg_name('regexp-mode'), default='contains', help='Mode of RegExp interpretation. Possible ones are [includes, matches, not_includes, not_matches]. Default is includes.')

        self.args = ['files', 'regexp', 'regexp-mode']
        self._add_config_to_args(parser)

    @_unpack_cmd
    @_unpack_yaml
    def __call__(self, files=None, regexp=None, regexp_mode='contains'):
        if isinstance(files, list):
            # directly process files list
            list_to_return = self._process_files_list(files)
            list_to_return = self._filter_with_regexp(list_to_return, regexp, regexp_mode)
            return list_to_return

        if os.path.exists(files):
            # it is not the glob-search path
            if os.path.isfile(files):
                # either list-file or single file mode
                if files.endswith('.'+self.lfe):
                    # it is file with list of files
                    list_to_return = self._process_list_file(files)
                    list_to_return = self._filter_with_regexp(list_to_return, regexp, regexp_mode)
                else:
                    # single file option
                    list_to_return = [files]
            else:
                # full directory to process
                list_to_return = self._process_directory(files)
                list_to_return = self._filter_with_regexp(list_to_return, regexp, regexp_mode)
        else:
            # glob search path
            list_to_return = self._process_glob(files)
            list_to_return = self._filter_with_regexp(list_to_return, regexp, regexp_mode)

        return list_to_return


def are_you_sure(message):
    while "the choice is invalid":
        choice = str(input(message + " Are you sure you want to do it? [y/n]"))
        if choice.lower() == 'y':
            return True
        elif choice.lower() == 'n':
            return False
        else:
            print('Unexpected input. Only y or n are accepted, sorry.')

class Matcher(MetaArger):
    def __init__(self, list_file_extension='txt', verbosity=False, args_prefix='output'):
        super().__init__(verbosity=verbosity, args_prefix=args_prefix, list_file_extension=list_file_extension)

    def _get_filename(self, addr, depth=-1, prefix=None, extension=None, name=None):
        if name is not None: # nothing to resolve
            return name

        file_name, file_ext = os.path.splitext(os.path.basename(addr))

        if depth != -1: # we need to go up the tree to find actual unique file name
            depth_counter = -1 * depth - 1
            cur_addr = addr
            for i in range(depth_counter):
                cur_addr = os.path.dirname(cur_addr)
            file_name = os.path.basename(cur_addr) + file_ext
        
        if prefix is not None: # we need to add prefix to each file
            file_name = '_'.join([prefix, file_name])
        
        if extension is not None: # we need to add/change extension of the file
            name = file_name + extension
        else:
            name = file_name + file_ext
        
        return name

    def add_args(self, parser):
        parser.add_argument('--'+self._get_arg_name('folder'), default=None,
                            help=f'''Output to work with.
                                    It could be either file list (only works with YAML configuration file), directory to write files to, or .{self.lfe} file containing one file address per line. 
                                    In case when nothing is provided source folder will be used.''')
        parser.add_argument('--'+self._get_arg_name('prefix'), default=None, help=f'Prefix to add to saved files')
        parser.add_argument('--'+self._get_arg_name('extension'), default=None, help=f'Extension to use for saving files')
        parser.add_argument('--'+self._get_arg_name('path_step'), default=None, help=f'Instead of original filename use folder name from higher level. Default is -1 -- file itself, -2 will be folder containing files etc.')
        parser.add_argument('-'+self._get_arg_name('force'), default=False, const=True, action='store_const', help='If file with the same name found it will be overwrited. By default this file will not be processed.')

        self.args = ['folder', 'prefix', 'extension', 'path_step', 'force']
        self._add_config_to_args(parser)

    @_unpack_cmd
    @_unpack_yaml
    def __call__(self, input_files, folder=None, prefix=None, extension=None, name=None, path_step=-1, force=False):
        if folder is None: # we are trying to write the same folder
           output_files = []
           for a in input_files:
               output_files.append(os.path.dirname(a), self._get_filename(a, path_step, prefix, extension, name))
        
        elif isinstance(folder, str) and os.path.isdir(folder): # configured as directory to output files
            dirname = folder
            output_files = []
            for a in input_files:
                output_files.append(os.path.join(dirname, self._get_filename(a, path_step, prefix, extension, name)))
        
        elif folder.endswith(self.lfe): # configured as file with list of direct outputs
            with open(folder) as f:
                output_files = f.read().split('\n')
            if len(output_files) != len(input_files):
                raise ValueError('Inconsistent input and output filenames')
        
        elif isinstance(folder, list): # configured as list of direct outputs
            output_files = folder
            if len(output_files) != len(input_files):
                raise ValueError('Inconsistent input and output filenames')

        else:
            raise ValueError('Configured unknown folder parameter. Please, check and reconfigure')
        
        good_pairs = []
        overwrite_pairs = []
        recurrent_pairs = []
        for inp_addr, outp_addr in zip(input_files, output_files):
            if os.path.exists(outp_addr):
                if os.path.samefile(inp_addr, outp_addr):
                    recurrent_pairs.append((inp_addr, outp_addr))
                    self._log(f'Same address: {inp_addr} -> {outp_addr}')
                else:
                    overwrite_pairs.append((inp_addr, outp_addr))
                    self._log(f'Existing address: {inp_addr} -> {outp_addr}')
            else:
                good_pairs.append((inp_addr, outp_addr))
                self._log(f'New address: {inp_addr} -> {outp_addr}')
        
        print(f'You tried to process {len(input_files)}, and here are your stats. Run with verbose to have all names listed.')

        final_pairs = []
        final_pairs += good_pairs
        print(f'- {len(good_pairs)} files will be created')

        if force:
            final_pairs += overwrite_pairs
            print(f'- {len(overwrite_pairs)} files will be overwritten')
            if len(recurrent_pairs) > 0:
                print(f'- {len(recurrent_pairs)} will be overwritten over the source files.')
                if are_you_sure(f'You are going to overwrite {len(recurrent_pairs)} source files.'):
                    final_pairs += overwrite_pairs

        return final_pairs


def add_args(parser, prefix=None):
    # left for the backwards compatibility
    exp = Expander(args_prefix=prefix)
    exp.add_args(parser)
