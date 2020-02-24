import os
import shutil

import torch
from yacs.config import CfgNode as _CfgNode

from torchline.utils import Logger


class CfgNode(_CfgNode):

    def _version(self):
        '''
        calculate the version of the configuration and logger
        '''
        def calc_version(path):
            if (not os.path.exists(path)) or len(os.listdir(path))==0:
                version = 0
            else:
                versions = [int(v.split('_')[-1]) for v in os.listdir(path)]
                version = max(versions)+1
            return version

        save_dir=self.trainer.default_save_path
        logger_name=self.trainer.logger.test_tube.name
        path = os.path.join(save_dir, logger_name)
        if self.trainer.logger.setting==0:
            version = calc_version(path)
        elif self.trainer.logger.setting==2:
            if self.trainer.logger.test_tube.version<0:
                version = calc_version(path)
            else:
                version = int(self.trainer.logger.test_tube.version)
        return version
    
    def setup_cfg_with_hparams(self, hparams):
        """
        Create configs and perform basic setups. 
        Args:
            hparams: arguments args from command line
        """
        self.merge_from_file(hparams.config_file)
        self.merge_from_list(hparams.opts)
        self.update({'hparams': hparams})

        version = self._version()
        save_dir=self.trainer.default_save_path
        logger_name=self.trainer.logger.test_tube.name
        self.log.path = os.path.join(save_dir, logger_name, f"version_{version}")
        self.log.name = os.path.join(self.log.path, 'log.txt')
        self.freeze()

        os.makedirs(self.log.path, exist_ok=True)
        
        # log.txt
        logger_print = Logger(__name__, self).getlogger()

        # copy config file
        src_cfg_file = hparams.config_file # source config file
        cfg_file_name = os.path.basename(src_cfg_file) # config file name
        dst_cfg_file = os.path.join(self.log.path, cfg_file_name)
        with open(dst_cfg_file, 'w') as f:
            f.write(str(self))

        if not (hparams.test_only or hparams.predict_only):
            torch.backends.cudnn.benchmark = False
        else:
            torch.backends.cudnn.benchmark = self.DEFAULT_CUDNN_BENCHMARK

        logger_print.info("Running with full config:\n{}".format(self))

global_cfg = CfgNode()

def get_cfg():
    '''
    Get a copy of the default config.

    Returns:
        a CfgNode instance.
    '''
    from .default import _C
    return _C.clone()