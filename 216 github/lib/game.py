#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心游戏逻辑
"""

import pygame
import time
from .android_adapter import android_adapter

class Game:
    def __init__(self, screen_width=720, screen_height=1280):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.running = False
        self.state = "menu"
        
    def start(self):
        self.running = True
        self.state = "playing"
        
    def pause(self):
        self.state = "paused"
        
    def resume(self):
        self.state = "playing"
        
    def stop(self):
        self.running = False
        self.state = "menu"