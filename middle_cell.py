import numpy as np

class MiddleCell:
    def __init__(self, cell_img, center, coords):
        self.image = cell_img
        self.center = center  # (x, y) position of the center of the middle
        self.xmin, self.w, self.ymin, self.h = coords
        self.symbol = self.find_symbol()

    def find_symbol(self):
        avg = np.mean(self.image[int(0.1*self.h):int(0.9*self.h), int(0.1*self.w):int(0.9*self.w)])
        if avg < 25:
            return '-'
        else:
            cavg = np.mean(self.image[int(0.38*self.h):int(0.62*self.h),
                                    int(0.38*self.w):int(0.62*self.w)])
            return 'x' if cavg > 80 else 'o'

