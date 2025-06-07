# A symmetrical gradient with a bright cyan core and deep blue edges.
from .utils.effects.color_source import MultiGradient

ocean_bands_gradient = MultiGradient(
    [
        ((0.6, 1.0, 0.5), 0.0),  # Start with a darker, deep blue (Value=0.5)
        ((0.5, 1.0, 1.0), 0.4),  # Fade into bright, full-value Cyan at 40%
        ((0.5, 1.0, 1.0), 0.6),  # Hold the bright Cyan for a solid band until 60%
        ((0.6, 1.0, 0.5), 1.0),  # Fade back out to the darker, deep blue at the end
    ]
)

# A flowing gradient from deep blue, through cyan, to a final bright green.
tropical_waters_gradient = MultiGradient(
    [
        ((0.66, 1.0, 1.0), 0.0),  # Start with a vibrant Deep Blue
        ((0.5, 1.0, 1.0), 0.5),  # Transition to bright Cyan by the 40% mark
        ((0.33, 1.0, 1.0), 1.0),  # Finish with a bright Green at the end
    ]
)

# Alternating dark and light colors to create a shimmering effect when scrolled.
ocean_shimmer_gradient = MultiGradient(
    [
        ((0.55, 0.8, 0.4), 0.0),  # Start with a dark, murky Teal
        ((0.5, 1.0, 1.0), 0.25),  # Pulse to bright Cyan
        ((0.55, 0.8, 0.4), 0.5),  # Back to dark Teal in the middle
        ((0.33, 1.0, 1.0), 0.75),  # Pulse to bright Green
        ((0.55, 0.8, 0.4), 1.0),  # End with dark Teal
    ]
)

flame_gradient = MultiGradient(
    [
        ((0.043, 1.0, 0.7), 0.0),  # Dim red/orange (Value = 0.4) # <-- CHANGED
        ((0.0, 1.0, 1.0), 0.4),  # Bright red (Value = 1.0)   # <-- CHANGED
        ((0.0, 1.0, 1.0), 0.6),  # Still bright red           # <-- CHANGED
        ((0.043, 1.0, 0.7), 1.0),  # Dim red/orange again       # <-- CHANGED
    ]
)
