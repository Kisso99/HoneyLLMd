# -*- coding: utf-8 -*-
from __future__ import division
import subprocess
import sys
import os

PY3_SCRIPT = os.path.join(os.path.dirname(__file__), "matrix_manager_py3.py")

class Matrix(object):
    def __init__(self,
                 counts_file="core/transition_counts_matrix.csv",
                 probs_file="core/transition_probabilities_matrix.csv",
                 initial_states=None,
                 epsilon=4.48e-8):
        self.counts_file = counts_file
        self.probs_file = probs_file
        self.epsilon = epsilon
        self.last_command = None
        self.state_order = []

        # 给 blocker 用的假属性，防止报错
        self.probs_df = None
        self.counts_df = None

    def _call(self, cmd_list):
        cmd = ["python3", PY3_SCRIPT] + cmd_list
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
            return output.strip()
        except Exception:
            return ""

    def update_matrix(self, src, dst, save=False):
        self._call([
            "update", src, dst, str(save),
            self.counts_file, self.probs_file, str(self.epsilon)
        ])
        self.last_command = src

    def find_optimal_pr(self, src, dst, probs_df=None, p_min=1e-9):
        res = self._call([
            "query", src, dst, str(p_min),
            self.counts_file, self.probs_file, str(self.epsilon)
        ])
        try:
            return float(res)
        except:
            return None

    def save_matrix(self):
        self._call([
            "save", self.counts_file, self.probs_file, str(self.epsilon)
        ])
