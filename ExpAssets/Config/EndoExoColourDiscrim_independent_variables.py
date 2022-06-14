from klibs.KLIndependentVariable import IndependentVariableSet

EndoExoColourDiscrim_ind_vars = IndependentVariableSet()

# Indicates if alerting signal involves a shift in intensity (volume)
EndoExoColourDiscrim_ind_vars.add_variable('signal_intensity', str)
EndoExoColourDiscrim_ind_vars['signal_intensity'].add_values('lo', 'hi')

# Time between cue onset (visual & audio) and target onset
EndoExoColourDiscrim_ind_vars.add_variable('cue_value', str)
EndoExoColourDiscrim_ind_vars['cue_value'].add_values('short', 'long')

# Indicates if cue accurately reflects target onset
EndoExoColourDiscrim_ind_vars.add_variable('cue_valid', bool)
EndoExoColourDiscrim_ind_vars['cue_valid'].add_values((True, 4), False)



