Use fast performance like numpy

Use clever and clean color logic to help performance and make code concise. 
This can include color theory, especially for calculating the next frame for gradient effects.
I am thinking of keeping a 1d array instance variable for the brightness of the leds. When calculate_next_frame is called, I can use a helper util function to apply a gradient to the entire array.