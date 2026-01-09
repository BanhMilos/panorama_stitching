# -*- coding:utf-8 -*-

import os
import time
import cv2
import imutils
import numpy as np
from stitching import Stitcher
from panorama_split import _build_uv_map_for_face, split_panorama_to_faces

DIR = './unconverted'
R_WIDTH = 8400
WIDTH = 8002
HEIGHT = 4001
BLACK_COLOR = 25
RESULT = './result.jpg'
files = os.listdir(DIR)


def remove_glare(img, brightness_thresh=230, saturation_thresh=60, min_mask_pixels=50, inpaint_radius=5):
    """Detect and inpaint specular glare regions before stitching."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    bright = cv2.threshold(v, brightness_thresh, 255, cv2.THRESH_BINARY)[1]
    low_sat = cv2.threshold(s, saturation_thresh, 255, cv2.THRESH_BINARY_INV)[1]
    mask = cv2.bitwise_and(bright, low_sat)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    if np.count_nonzero(mask) < min_mask_pixels:
        return img

    return cv2.inpaint(img, mask, inpaint_radius, cv2.INPAINT_TELEA)

def stitch(files):
    imgs = []
    for file in files:
        raw = cv2.imread(DIR + '/' + file)
        if raw is None:
            continue
        imgs.append(raw)
        #imgs.append(remove_glare(raw))
    stitcher = Stitcher(detector="brisk", confidence_threshold=0.3, matches_graph_dot_file = "matches.dot" )
    pano = stitcher.stitch(imgs)
    if pano is not None:
        return pano
    else: 
        return None

def crop(img):
    width, height = img.shape[1], img.shape[0]
    if width > R_WIDTH:
        img = imutils.resize(img, width=R_WIDTH)
        width, height = img.shape[1], img.shape[0]

    top, bottom = 0, height
    limit = int(height/8)
    top_limit = limit
    bottom_limit = height - limit

    # top
    c = 0
    while c < width:
        r = 0
        while r < top_limit:
            if sum(img[r,c]) < BLACK_COLOR:
                r = r + 1
            else:
                if r > top:
                    top = r
                break
        c = c + 1
    top = top + 1

    # bottom
    c = 0
    while c < width:
        r = height - 1
        while r > bottom_limit:
            if sum(img[r,c]) < BLACK_COLOR:
                r = r - 1
            else:
                if r < bottom:
                    bottom = r
                break
        c = c + 1
    bottom = bottom -1

    # 裁掉上下的黑边
    tmp = img[top:bottom, 0:width]
    width, height = tmp.shape[1], tmp.shape[0]
    limit = int(height/8)
    left, right = 0, width
    left_limit = limit
    right_limit = width - limit

    # left
    r = 0
    while r < height:
        c = 0
        while c < left_limit:
            if sum(tmp[r,c]) < BLACK_COLOR:
                c = c + 1
            else:
                if c > left:
                    left = c
                break
        r = r + 1

    # right
    r = 0
    while r < height:
        c = width - 1
        while c > right_limit:
            if sum(tmp[r,c]) < BLACK_COLOR:
                c = c - 1
            else:
                if c < right:
                    right = c
                break
        r = r + 1

    # 裁掉左右的黑边
    tmp = tmp[0:height, left:right]
    return tmp

def panorToEquirectangular(pano):
    """Convert cubemap (arranged as 6 faces) to equirectangular panorama."""
    face_size = pano.shape[0]
    # Assume input pano is already 6 cube faces arranged; extract them
    faces = split_panorama_to_faces(pano, face_size=face_size)
    
    # Create equirectangular output
    h, w = face_size, face_size * 2
    equirect_img = np.zeros((h, w, 3), dtype=np.uint8)
    
    # For each pixel in the equirectangular image, sample from the appropriate cube face
    for y in range(h):
        for x in range(w):
            # Convert pixel to spherical coordinates
            lon = (x / w) * 2.0 * np.pi - np.pi
            lat = (y / h) * np.pi - np.pi / 2.0
            
            # Convert to 3D direction vector
            cos_lat = np.cos(lat)
            dx = cos_lat * np.sin(lon)
            dy = np.sin(lat)
            dz = cos_lat * np.cos(lon)
            
            # Determine which cube face and get UV coordinates
            abs_x, abs_y, abs_z = abs(dx), abs(dy), abs(dz)
            
            if abs_x >= abs_y and abs_x >= abs_z:
                # X-axis dominant
                if dx > 0:
                    face_name = 'right'
                    u = -dz / abs_x
                    v = dy / abs_x
                else:
                    face_name = 'left'
                    u = dz / abs_x
                    v = dy / abs_x
            elif abs_y >= abs_x and abs_y >= abs_z:
                # Y-axis dominant
                if dy > 0:
                    face_name = 'top'
                    u = dx / abs_y
                    v = -dz / abs_y
                else:
                    face_name = 'bottom'
                    u = dx / abs_y
                    v = dz / abs_y
            else:
                # Z-axis dominant
                if dz > 0:
                    face_name = 'front'
                    u = dx / abs_z
                    v = dy / abs_z
                else:
                    face_name = 'back'
                    u = -dx / abs_z
                    v = dy / abs_z
            
            # Convert UV from [-1,1] to pixel coordinates
            px = int((u + 1.0) / 2.0 * (face_size - 1))
            py = int((v + 1.0) / 2.0 * (face_size - 1))
            
            # Clamp to valid range
            px = np.clip(px, 0, face_size - 1)
            py = np.clip(py, 0, face_size - 1)
            
            # Sample from appropriate face
            face_img = faces[face_name]
            equirect_img[y, x] = face_img[py, px]
    
    return equirect_img

def complement_sky(pano):
    tmp = imutils.resize(pano, width=WIDTH)
    rows, cols = tmp.shape[:2]
    border = HEIGHT - rows

    sky = cv2.imread('sky.jpg')
    sky = imutils.resize(sky, width=WIDTH)
    sky_rows = sky.shape[0]
    start = sky_rows - border
    sky = sky[start:sky_rows]

    # 扩展到w:h=2:1
    img = np.vstack((sky[:,:], tmp[:,:]))

    mark = np.zeros((HEIGHT, WIDTH), np.uint8)
    color = (0, 0, 0)
    mark[0:border,0:cols] = 255

    # 用inpaint方法修复
    img = cv2.inpaint(img, mark, 3, cv2.INPAINT_TELEA)

    # 将天空混合
    tmp_sky = img[0:border,:]
    sky = cv2.addWeighted(tmp_sky, 0.7, sky, 0.3, 0.0)
    img = np.vstack((sky[:,:], img[border:,:]))

    # 对边界进行渐入渐出融合
    start = border - 1
    end = start - 100
    blend = 0.01
    for r in range(start, end, -1):
        img[r,:] = tmp[0,:] * (1 - blend) + sky[r,:] * blend
        blend = blend + 0.01

    # 左右各裁掉1像素，避免黑线出现
    rows, cols = img.shape[:2]
    img = img[1:,1:cols-1]

    # 边界边缘再高斯模糊
    tmp = img[0:border+100, :]
    tmp = cv2.GaussianBlur(tmp, (9, 9), 2.5)
    img = np.vstack((tmp[:,:], img[border+100:,:]))

    return img

if __name__ == '__main__':
    start = time.time()
    files = os.listdir(DIR)
    pano = stitch(files)
    print('stitch done')
    cv2.resize(pano, (800, 400)),
    if pano is not None:
        cv2.imshow('pano', pano)
        pano = panorToEquirectangular(pano)
        print('panorToEquirectangular done')
        cv2.imwrite('pano.jpg', pano)
        print('panorToEquirectangular saved')
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        pano = crop(pano)
        print('crop done')
        # pano = complement_sky(pano)
        cv2.imwrite(RESULT, pano)
    else:
        print('error')
    end = time.time()
    print('cost ' + str(end-start))