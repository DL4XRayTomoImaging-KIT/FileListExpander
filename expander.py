from glob import glob
import re
import os

class Expander:
    def __init__(self, list_file_extension='txt', verbosity=False, files_only=True):
        self.lfe = list_file_extension
        self.v = verbosity
        self.fo = files_only

    def _log(self, m):
        if self.v:
            print(m)

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

    def expand_file_list(self, main_addr, regexp=None, regexp_option='contains'):
        if isinstance(main_addr, list):
            # directly process files list
            list_to_return = self._process_files_list(main_addr)
            list_to_return = self._filter_with_regexp(list_to_return, regexp, regexp_option)
            return list_to_return

        if os.path.exists(main_addr):
            # it is not the glob-search path
            if os.path.isfile(main_addr):
                # either list-file or single file mode
                if main_addr.endswith('.'+self.lfe):
                    # it is file with list of files
                    list_to_return = self._process_list_file(main_addr)
                    list_to_return = self._filter_with_regexp(list_to_return, regexp, regexp_option)
                else:
                    # single file option
                    list_to_return = [main_addr]
            else:
                # full directory to process
                list_to_return = self._process_directory(main_addr)
                list_to_return = self._filter_with_regexp(list_to_return, regexp, regexp_option)
        else:
            # glob search path
            list_to_return = self._process_glob(main_addr)
            list_to_return = self._filter_with_regexp(list_to_return, regexp, regexp_option)

        return list_to_return

    def __call__(self, main_addr, regexp=None, regexp_option='contains'):
        return self.expand_file_list(main_addr, regexp, regexp_option)
