# -*- coding: utf-8 -*-

# # #
#
# Endo/Exo Audio Signalling task w/ ColourWheel Detect & Discrim
# Fix -> audio -> colour stim -> mask -> Wheel
# Speeded detection, then discrimination
#
__author__ = "Brett Feltmate"

import klibs
import numpy.random
from klibs import P
from klibs.KLConstants import TK_MS, RC_KEYPRESS, RC_COLORSELECT
from klibs.KLGraphics.colorspaces import const_lum
from klibs.KLUtilities import deg_to_px, now, mouse_pos
from klibs.KLUserInterface import ui_request, any_key
from klibs.KLCommunication import message
from klibs.KLGraphics import fill, blit, flip, clear
from klibs.KLGraphics import KLDraw as kld
from klibs.KLResponseCollectors import ResponseCollector, KeyMap
from klibs.KLAudio import Noise
from sdl2 import SDLK_SPACE
import aggdraw # For drawing mask cells in a single texture
from PIL import Image
import random

WHITE = (255, 255, 255, 255)
PRE = "pre_cue"
CUE = "cue"
POST = 'post_cue'

class EndoExoColourDiscrim(klibs.Experiment):

	def setup(self):
		self.sizes = {
			'cue': deg_to_px(P.cue_size),
			'target': deg_to_px(P.target_size),
			'wheel': [deg_to_px(P.wheel_size[0]), deg_to_px(P.wheel_size[1])],
			'cursor': [deg_to_px(P.cursor_size[0]), deg_to_px(P.cursor_size[1])] # diameter, thickness
		}

		self.txtm.add_style('cue', font_size=self.sizes['cue'])

		self.stims = {
			'cue_long': message('-------', style='cue', location=P.screen_c, registration=5, blit_txt=False),
			'cue_short': message('----', style='cue', location=P.screen_c, registration=5, blit_txt=False),
			'target': kld.Rectangle(width=self.sizes['target']),
			'wheel': kld.ColorWheel(diameter=self.sizes['wheel'][0], thickness=self.sizes['wheel'][1], auto_draw=False),
			'cursor': kld.Annulus(diameter=self.sizes['cursor'][0], thickness=self.sizes['cursor'][1], fill=WHITE)
		}



		self.rc_key = ResponseCollector(uses=RC_KEYPRESS)
		self.rc_wheel = ResponseCollector(uses=RC_COLORSELECT)
		self.rc_wheel.color_listener.color_response = True
		self.keymap = KeyMap(
			name='response',
			ui_labels=['space'],
			data_labels=['detected'],
			keycodes=[SDLK_SPACE]
		)





	def block(self):
		fill()
		message("Hey", location=P.screen_c, registration=5, blit_txt=True)
		flip()

		any_key()

		fill()
		message("What are you wearing?", location=P.screen_c, registration=5, blit_txt=True)
		flip()

		any_key()

		fill()
		message("Nice", location=P.screen_c, registration=5, blit_txt=True)
		flip()

		any_key()

		fill()
		message("anyways...", location=P.screen_c, registration=5, blit_txt=True)
		flip()

		any_key()

		fill()
		message("Here's the task:", location=P.screen_c, registration=5, blit_txt=True)
		flip()

		any_key()

	def setup_response_collector(self):
		self.rc_key.terminate_after = [P.detection_timeout, TK_MS]
		self.rc_key.display_callback = self.detection_callback
		self.rc_key.keypress_listener.terminates = True
		self.rc_key.keypress_listener.key_map = self.keymap

		self.rc_wheel.terminate_after = [P.discrimination_timeout, TK_MS]
		self.rc_wheel.display_callback = self.discrimination_callback
		self.rc_wheel.color_listener.set_wheel(self.stims['wheel'])
		self.rc_wheel.color_listener.set_target(self.stims['target'])


	def trial_prep(self):
		self.fixation_duration = self.get_fixation_interval()
		self.signals = self.generate_signals()



		self.stims['mask'] = self.generate_mask()
		if self.soa == 400:
			self.trial_cue = 'cue_short' if self.cue_valid else 'cue_long'
		else:
			self.trial_cue = 'cue_long' if self.cue_valid else 'cue_long'

		self.target_angle = numpy.random.randint(0, 360)
		self.target_rgb = self.stims['wheel'].color_from_angle(self.target_angle)
		self.stims['target'].fill = self.target_rgb

		self.stims['wheel'].rotation = numpy.random.randint(0, 360)

		events = []
		events.append([self.fixation_duration, 'play_cue'])
		events.append([events[-1][0] + P.signal_duration, 'stop_cue'])
		events.append([events[-1][0] + self.soa, 'target_on'])
		events.append([events[-1][0] + P.target_duration, 'mask_on'])

		for e in events:
			self.evm.register_ticket([e[1], e[0]])


	def trial(self):
		self.signals[PRE].play()

		fill()
		blit(self.stims[self.trial_cue], location=P.screen_c, registration=5)
		flip()

		while self.signals[PRE].playing:
			ui_request()

		self.signals[CUE].play()

		while self.signals[CUE].playing:
			ui_request()

		self.signals[POST].play()

		while self.evm.before('target_on'):
			ui_request()

		fill()
		blit(self.stims['target'], registration=5, location=P.screen_c)
		flip()



		self.rc_key.collect()
		detection = self.rc_key.keypress_listener.response()

		self.rc_wheel.collect()

		discrimination = self.rc_wheel.color_listener.response()

		return {
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"fix_duration": self.fixation_duration,
			"soa": self.soa,
			"cue_valid": self.cue_valid,
			"signal_intensity": self.signal_intensity,
			"target_rgb": self.target_rgb,
			"response_rgb": discrimination.value[1],
			"detection_rt": detection.rt,
			"discrimination_rt": discrimination.rt,
			"discrimination_error": discrimination.value[0]
		}

	def trial_clean_up(self):
		clear()

		self.rc_key.keypress_listener.reset()
		self.rc_wheel.color_listener.reset()

		while self.signals['post_cue'].playing:
			ui_request()



	def clean_up(self):
		pass

	def detection_callback(self):
		if self.evm.after('mask_on'):

			fill()
			blit(self.stims['mask'], registration=5, location=P.screen_c)
			flip()

	def discrimination_callback(self):

		fill()
		blit(self.stims['wheel'], location=P.screen_c, registration=5)
		blit(self.stims['cursor'], location=mouse_pos(), registration=5)
		flip()


	def generate_signals(self):
		pre_cue = Noise(
			duration=self.fixation_duration * 2,
			dichotic=False,
			volume=0.1
		)
		cue_volume = 0.2 if self.signal_intensity == 'hi' else 0.1
		cue = Noise(
			duration=P.signal_duration*2,
			dichotic=True,
			volume=cue_volume
		)

		post_cue_duration = self.soa + P.target_duration + P.detection_timeout + P.discrimination_timeout + P.ITI

		post_cue = Noise(
			duration=post_cue_duration*2,
			dichotic=False,
			volume=0.1
		)

		return {PRE: pre_cue, CUE: cue, POST: post_cue}


	def get_fixation_interval(self):
		max_f, min_f, mean_f = P.fixation_max, P.fixation_min, P.fixation_mean

		interval = random.expovariate(1 / (mean_f - min_f)) + min_f
		while interval > max_f:
			interval = random.expovariate(1 / (mean_f - min_f)) + min_f


		return interval



	def generate_mask(self):
		# Set mask size
		canvas_size = self.sizes['target']
		# Set cell size
		cell_size = canvas_size / 2 # Mask comprised of 4 smaller cells arranged 2x2
		# Each cell has a black outline
		cell_outline_width = deg_to_px(.05)

		# Initialize canvas to be painted w/ mask cells
		canvas = Image.new('RGBA', [canvas_size, canvas_size], (0, 0, 0, 0))

		surface = aggdraw.Draw(canvas)

		# Initialize pen to draw cell outlines
		transparent_pen = aggdraw.Pen((0, 0, 0), cell_outline_width)

		# Generate cells, arranged in 4x4 array
		for row in [0, 1]:
			for col in [0, 1]:
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

		return numpy.asarray(canvas)




