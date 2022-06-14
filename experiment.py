# -*- coding: utf-8 -*-

# # #
#
# Endo/Exo Audio Signalling task w/ ColourWheel Detect & Discrim
# Fix -> audio -> colour stim -> mask -> Wheel
# Speeded detection, then discrimination
#
__author__ = "Brett Feltmate"

import klibs
import numpy as np
from klibs import P
from klibs.KLConstants import TK_MS, RC_KEYPRESS, RC_COLORSELECT, NO_RESPONSE
from klibs.KLGraphics.colorspaces import const_lum
from klibs.KLUtilities import deg_to_px, now, mouse_pos, hide_mouse_cursor, show_mouse_cursor
from klibs.KLUserInterface import ui_request, any_key
from klibs.KLCommunication import message
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLGraphics import KLDraw as kld
from klibs.KLResponseCollectors import ResponseCollector, KeyMap, MouseButtonResponse, Response
from klibs.KLAudio import AudioClip

import aggdraw # For drawing mask cells in a single texture
from PIL import Image
import random
import math


WHITE = (255, 255, 255, 255)
PRE = "pre_cue"
CUE = "cue"
POST = 'post_cue'
SHORT = 'short'
LONG = 'long'
TARGET = 'target'
WHEEL = 'wheel'
CURSOR = 'cursor'
MASK = 'mask'
VALID = 'valid'
INVALID_SHORT = 'invalid_short'
INVALID_LONG = 'invalid_long'
FIX = 'fixation'
CATCH = 'catch'

class EndoExoColourDiscrim(klibs.Experiment):

	def setup(self):

		# Probably overthinking this.
		# Used to select appropriate SOA list for trial (based on cue type & validity),
		# from which a value is randomly selected.
		self.ctoa_map = {
			SHORT: {
				VALID: 400,
				INVALID_SHORT: 1000,
				INVALID_LONG: 1600
			},
			LONG: {
				VALID: 1600,
				INVALID_SHORT: 400,
				INVALID_LONG: 1000
			}
		}

		self.sizes = {
			CUE: deg_to_px(P.cue_size),
			TARGET: deg_to_px(P.target_size),
			WHEEL: [deg_to_px(P.wheel_size[0]), deg_to_px(P.wheel_size[1])],
			CURSOR: [deg_to_px(P.cursor_size[0]), deg_to_px(P.cursor_size[1])] # diameter, thickness
		}

		self.txtm.add_style(CUE, font_size=self.sizes[CUE])

		self.stims = {
			LONG: message('-------', style=CUE, location=P.screen_c, registration=5, blit_txt=False),
			SHORT: message('----', style=CUE, location=P.screen_c, registration=5, blit_txt=False),
			TARGET: kld.Rectangle(width=self.sizes[TARGET]),
			WHEEL: kld.ColorWheel(diameter=self.sizes[WHEEL][0], thickness=self.sizes[WHEEL][1], auto_draw=False),
			CURSOR: kld.Annulus(diameter=self.sizes[CURSOR][0], thickness=self.sizes[CURSOR][1], fill=WHITE),
			FIX: kld.FixationCross(size=self.sizes[TARGET], thickness=deg_to_px(0.1), fill=WHITE)
		}



		self.rc_wheel = ResponseCollector(uses=RC_COLORSELECT)
		self.rc_wheel.color_listener.color_response = True

		self.rc_mouse = ResponseCollector(uses=[MouseButtonResponse])



		if P.run_practice_blocks:
			self.insert_practice_block(1, trial_counts=15)




	def block(self):

		# fill()
		# message("Hey", location=P.screen_c, registration=5, blit_txt=True)
		# flip()
		#
		# any_key()
		#
		# fill()
		# message("What are you wearing?", location=P.screen_c, registration=5, blit_txt=True)
		# flip()
		#
		# any_key()
		#
		# fill()
		# message("Nice", location=P.screen_c, registration=5, blit_txt=True)
		# flip()
		#
		# any_key()
		#
		# fill()
		# message("anyways...", location=P.screen_c, registration=5, blit_txt=True)
		# flip()
		#
		# any_key()
		#
		# fill()
		# message("Here's the task:", location=P.screen_c, registration=5, blit_txt=True)
		# flip()
		#
		# any_key()
		pass

	def setup_response_collector(self):
		self.rc_mouse.terminate_after = [P.detection_timeout, TK_MS]
		self.rc_mouse.display_callback = self.detection_callback
		self.rc_mouse.mousebutton_listener.terminates = True
		self.rc_mouse.mousebutton_listener.buttonmap = {'left': 'detected'}

		self.rc_wheel.terminate_after = [P.discrimination_timeout, TK_MS]
		self.rc_wheel.display_callback = self.discrimination_callback



	def trial_prep(self):
		if P.trial_number == P.trials_per_block / 2:
			fill()
			message("Good job!\nTake a break!\nPress any key to continue...", location=P.screen_c, registration=5, blit_txt=True)
			flip()

			any_key()



		self.ctoa = self.ctoa_map[self.cue_value][self.cue_valid] if not self.catch_trial else 1600
		self.fixation_duration = self.get_fixation_interval()
		self.trial_audio = self.get_trial_audio()

		self.base_volume = 0.1
		self.cue_volume = 0.2 if self.signal_intensity == 'hi' else self.base_volume

		if not self.catch_trial:
			self.stims[MASK] = self.generate_mask()
			self.stims[WHEEL].rotation = np.random.randint(0, 360)
			self.stims[WHEEL].render()

			self.target_angle = np.random.randint(0, 360)
			self.target_rgb = self.stims[WHEEL].color_from_angle(self.target_angle)
			self.stims[TARGET].fill = self.target_rgb

			self.rc_wheel.color_listener.set_wheel(self.stims[WHEEL])
			self.rc_wheel.color_listener.set_target(self.stims[TARGET])

		events = []
		events.append([self.fixation_duration, 'play_cue'])
		events.append([events[-1][0] + P.cue_duration, 'stop_cue'])
		events.append([events[-1][0] + self.ctoa, 'target_on'])
		events.append([events[-1][0] + P.target_duration, 'mask_on'])

		for e in events:
			self.evm.register_ticket([e[1], e[0]])




	def trial(self):
		hide_mouse_cursor()
		self.trial_audio.play()

		fill()
		blit(self.stims[self.cue_value], location=P.screen_c, registration=5)
		flip()

		while self.evm.before('play_cue'):
			ui_request()

		self.trial_audio.volume = self.cue_volume

		while self.evm.before('stop_cue'):
			ui_request()

		self.trial_audio.volume = self.base_volume

		while self.evm.before('target_on'):
			ui_request()

		if not self.catch_trial:

			fill()
			blit(self.stims[TARGET], registration=5, location=P.screen_c)
			flip()



			self.rc_mouse.collect()
			detection = self.rc_mouse.mousebutton_listener.response()

			if detection[0] == NO_RESPONSE:
				discrimination = Response(NO_RESPONSE, 'NA')
				if P.practicing:
					fb_start = now()
					fill()
					message("Too slow!", location=P.screen_c, registration=5, blit_txt=True)
					flip()

					while now() < fb_start + (P.feedback_duration/1000):
						ui_request()

			else:
				show_mouse_cursor()
				self.rc_wheel.collect()
				discrimination = self.rc_wheel.color_listener.response()

		return {
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"fix_duration": self.fixation_duration,
			"ctoa": self.ctoa,
			"cue_valid": CATCH if self.catch_trial else self.cue_valid,
			"signal_intensity": self.signal_intensity,
			"target_rgb": CATCH if self.catch_trial else self.target_rgb,
			"response_rgb": CATCH if self.catch_trial else detection.value[1],
			"detection_rt": CATCH if self.catch_trial else detection.rt,
			"discrimination_rt": CATCH if self.catch_trial else discrimination.rt,
			"discrimination_error": CATCH if self.catch_trial else discrimination.value[0]
		}

	def trial_clean_up(self):
		self.rc_mouse.mousebutton_listener.reset()
		self.rc_wheel.color_listener.reset()

		fill()
		blit(self.stims[FIX], location=P.screen_c, registration=5)
		flip()

		ITI_start = now()

		while now() < ITI_start + (P.ITI / 1000):
			ui_request()

		self.trial_audio.stop()



	def clean_up(self):
		pass

	def detection_callback(self):
		if self.evm.after('mask_on'):

			fill()
			blit(self.stims[MASK], registration=5, location=P.screen_c)
			flip()

	def discrimination_callback(self):

		fill()
		blit(self.stims[WHEEL], location=P.screen_c, registration=5)
		blit(self.stims[CURSOR], location=mouse_pos(), registration=5)
		flip()


	def get_trial_audio(self):
		fix_L = self.generate_noise(self.fixation_duration)
		fix_R = fix_L

		fix = np.c_[fix_L, fix_R]

		cue_L = self.generate_noise(P.cue_duration)
		cue_R = self.generate_noise(P.cue_duration)

		cue = np.c_[cue_L, cue_R]

		post_duration = self.ctoa + P.target_duration + P.detection_timeout + P.discrimination_timeout + P.ITI + 1000
		post_L = self.generate_noise(post_duration)
		post_R = post_L

		post = np.c_[post_L, post_R]

		clip = np.r_[fix, cue, post]

		return AudioClip(clip=clip, volume=0.1)


	def generate_noise(self, duration):
		max_int = 2**16/2 - 1 # 32767, which is the max/min value for a signed 16-bit int
		dtype = np.int16 # Default audio format for SDL_Mixer is signed 16-bit integer
		sample_rate = 44100/2 # sample rate for each channel is 22050 kHz, so 44100 total.
		size = int((duration/1000.0)*sample_rate) * 2

		arr = np.random.uniform(low=-1.0, high=1.0, size=size) * max_int

		return arr.astype(dtype)


	def get_fixation_interval(self):
		max_f, min_f, mean_f = P.fixation_max, P.fixation_min, P.fixation_mean

		interval = random.expovariate(1.0 / float(mean_f - min_f)) + min_f
		while interval > max_f:
			interval = random.expovariate(1.0 / float(mean_f - min_f)) + min_f


		return interval



	def generate_mask(self):
		cells = 16
		# Set mask size
		canvas_size = self.sizes[TARGET]
		# Set cell size
		cell_size = int(canvas_size / math.sqrt(cells)) # Mask comprised of 4 smaller cells arranged 2x2
		# Each cell has a black outline
		cell_outline_width = deg_to_px(.05)

		# Initialize canvas to be painted w/ mask cells
		canvas = Image.new('RGBA', [canvas_size, canvas_size], (0, 0, 0, 0))

		surface = aggdraw.Draw(canvas)

		# Initialize pen to draw cell outlines
		transparent_pen = aggdraw.Pen((0, 0, 0), cell_outline_width)

		# Generate cells, arranged in 4x4 array
		for row in range(cell_size):
			for col in range(cell_size):
				# Randomly select colour for each cell
				cell_colour = const_lum[random.randrange(0, 360)]
				# Brush to apply colour
				colour_brush = aggdraw.Brush(tuple(cell_colour[:3]))
				# Determine cell boundary coords
				top_left = (row * cell_size, col * cell_size)
				bottom_right = ((row+1) * cell_size, (col+1) * cell_size)
				# Create cell
				surface.rectangle(
					(top_left[0], top_left[1], bottom_right[0], bottom_right[1]),
					transparent_pen,
					colour_brush)
		# Apply cells to mask
		surface.flush()

		return np.asarray(canvas)





