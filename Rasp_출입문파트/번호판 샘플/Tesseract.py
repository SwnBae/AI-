import cv2
import numpy as np
import matplotlib.pyplot as plt
import pytesseract


def find_plate(samplev):
    plt.style.use('dark_background')
 
    img_ori = cv2.imread(samplev)

    height, width, channel = img_ori.shape

    gray = cv2.cvtColor(img_ori, cv2.COLOR_BGR2GRAY)

    #클로징, 오프닝 연산
    structuringElement = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    imgClosing = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, structuringElement)
    imgOpening = cv2.morphologyEx(gray, cv2.MORPH_OPEN, structuringElement)

    gray = cv2.subtract(gray, cv2.subtract(imgClosing, gray))
    gray = cv2.add(gray, cv2.subtract(gray, imgOpening))

    ''' ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    plt.figure(figsize=(12, 10))
    plt.imshow(gray, cmap='gray')
    plt.show()
    '''
    
    #가우시안 블러
    
    img_blurred = cv2.GaussianBlur(gray, ksize=(5, 5), sigmaX=0)
    '''ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    plt.figure(figsize=(12, 10))
    plt.imshow(img_blurred, cmap='gray')
    plt.show()
    '''

    img_thresh = cv2.adaptiveThreshold(
        img_blurred, 
        maxValue=255.0, 
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        thresholdType=cv2.THRESH_BINARY_INV, 
        blockSize=13, 
        C=9
    )
    

    #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    plt.figure(figsize=(12, 10))
    plt.imshow(img_thresh, cmap='gray')
    plt.show()

    #윤곽선 찾기

    contours, _ = cv2.findContours(
        img_thresh, 
        mode=cv2.RETR_LIST, 
        method=cv2.CHAIN_APPROX_SIMPLE
    )
    #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    temp_result = np.zeros((height, width, channel), dtype=np.uint8)
    
    cv2.drawContours(temp_result, contours=contours, contourIdx=-1, color=(255, 255, 255))

    plt.figure(figsize=(12, 10))
    plt.imshow(temp_result, cmap='gray')
    plt.show()


    # 윤곽선의 사각형 정보 찾기

    temp_result = np.zeros((height, width, channel), dtype=np.uint8)

    contours_dict = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        cv2.rectangle(temp_result, pt1=(x, y), pt2=(x+w, y+h), color=(255, 255, 255), thickness=2)
    
        # insert to dict
        contours_dict.append({
            'contour': contour,
            'x': x,
            'y': y,
            'w': w,
            'h': h,
            'cx': x + (w / 2),
            'cy': y + (h / 2)
        })


    #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    plt.figure(figsize=(12, 10))
    plt.imshow(temp_result, cmap='gray')
    plt.show()

    #번호판 문자의 규격 이용, 번호판 후보군 찾기

    MIN_AREA = 80
    MIN_WIDTH, MIN_HEIGHT = 2, 8
    MIN_RATIO, MAX_RATIO = 0.25, 1.0
    
    possible_contours = []

    cnt = 0
    for d in contours_dict:
        area = d['w'] * d['h']
        ratio = d['w'] / d['h']
    
        if area > MIN_AREA \
        and d['w'] > MIN_WIDTH and d['h'] > MIN_HEIGHT \
        and MIN_RATIO < ratio < MAX_RATIO:
            d['idx'] = cnt
            cnt += 1
            possible_contours.append(d)
        
    #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    temp_result = np.zeros((height, width, channel), dtype=np.uint8)
    
    for d in possible_contours:
        cv2.rectangle(temp_result, pt1=(d['x'], d['y']), pt2=(d['x']+d['w'], d['y']+d['h']), color=(255, 255, 255), thickness=2)

    #print(len(possible_contours))
    plt.figure(figsize=(12, 10))
    plt.imshow(temp_result, cmap='gray')
    plt.show()

    #후보군 중 실제 번호판 찾아내기
    MAX_DIAG_MULTIPLYER = 5 
    MAX_ANGLE_DIFF = 10.0
    MAX_AREA_DIFF = 0.5 
    MAX_WIDTH_DIFF = 0.8
    MAX_HEIGHT_DIFF = 0.2
    MIN_N_MATCHED = 6
    MAX_N_MATCHED = 9

    def find_chars(contour_list):
        matched_result_idx = []
        
        for d1 in contour_list:
            matched_contours_idx = []
            for d2 in contour_list:
                if d1['idx'] == d2['idx']:
                    continue

                dx = abs(d1['cx'] - d2['cx'])
                dy = abs(d1['cy'] - d2['cy'])

                diagonal_length1 = np.sqrt(d1['w'] ** 2 + d1['h'] ** 2)
    
                distance = np.linalg.norm(np.array([d1['cx'], d1['cy']]) - np.array([d2['cx'], d2['cy']]))
                if dx == 0:
                    angle_diff = 90
                else:
                    angle_diff = np.degrees(np.arctan(dy / dx))
                area_diff = abs(d1['w'] * d1['h'] - d2['w'] * d2['h']) / (d1['w'] * d1['h'])
                width_diff = abs(d1['w'] - d2['w']) / d1['w']
                height_diff = abs(d1['h'] - d2['h']) / d1['h']
    
                if distance < diagonal_length1 * MAX_DIAG_MULTIPLYER \
                and angle_diff < MAX_ANGLE_DIFF and area_diff < MAX_AREA_DIFF \
                and width_diff < MAX_WIDTH_DIFF and height_diff < MAX_HEIGHT_DIFF:
                    matched_contours_idx.append(d2['idx'])

            # append this contour
            matched_contours_idx.append(d1['idx'])

            if len(matched_contours_idx) < MIN_N_MATCHED or len(matched_contours_idx) > MAX_N_MATCHED:
                continue

            matched_result_idx.append(matched_contours_idx)

            #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
            #print("함수 내 매치드 사각형, 자동차 번호 개수")
            #print(len(matched_contours_idx))
            #print(matched_contours_idx)
            #print(d1['idx'])
        
            break

        print("-번호판 찾기 유무-")
    
        if len(matched_result_idx) == 1:
            print("번호판을 찾았습니다!")
        else:
            print("번호판을 찾지 못했습니다.")
        return matched_result_idx
    
    result_idx = find_chars(possible_contours)
    #print(result_idx)

    matched_result = []
    for idx_list in result_idx:
        matched_result.append(np.take(possible_contours, idx_list))


    #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    #print(matched_result)
    
    #최종 번호판 영역 결과
    temp_result = np.zeros((height, width, channel), dtype=np.uint8)

    for r in matched_result:
        for d in r:
          cv2.rectangle(temp_result, pt1=(d['x'], d['y']), pt2=(d['x']+d['w'], d['y']+d['h']),color=(255, 255, 255), thickness=2)

    plt.figure(figsize=(12, 10))
    plt.imshow(temp_result, cmap='gray')
    plt.show()

    #번호판 돌리기
    PLATE_WIDTH_PADDING = 1.3 
    PLATE_HEIGHT_PADDING = 1.5 
    MIN_PLATE_RATIO = 3
    MAX_PLATE_RATIO = 10

    plate_imgs = []
    plate_infos = []

    for i, matched_chars in enumerate(matched_result):
        sorted_chars = sorted(matched_chars, key=lambda x: x['cx'])

        plate_cx = (sorted_chars[0]['cx'] + sorted_chars[-1]['cx']) / 2
        plate_cy = (sorted_chars[0]['cy'] + sorted_chars[-1]['cy']) / 2
    
        plate_width = (sorted_chars[-1]['x'] + sorted_chars[-1]['w'] - sorted_chars[0]['x']) * PLATE_WIDTH_PADDING
    
        sum_height = 0
        for d in sorted_chars:
            sum_height += d['h']

        plate_height = int(sum_height / len(sorted_chars) * PLATE_HEIGHT_PADDING)
    
        triangle_height = sorted_chars[-1]['cy'] - sorted_chars[0]['cy']
        triangle_width = sorted_chars[-1]['cx'] - sorted_chars[0]['cx']

        angle = np.degrees(np.arctan2(triangle_height, triangle_width))

    
        rotation_matrix = cv2.getRotationMatrix2D(center=(plate_cx, plate_cy), angle=angle, scale=1.0)
    
        img_rotated = cv2.warpAffine(img_thresh, M=rotation_matrix, dsize=(width, height))

        '''
        #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
        plt.subplot(len(matched_result), 1, i+1)
        plt.imshow(img_rotated, cmap='gray')
        plt.show()
        '''
    
        img_cropped = cv2.getRectSubPix(
            img_rotated, 
            patchSize=(int(plate_width), int(plate_height)), 
            center=(int(plate_cx), int(plate_cy))
        )
    
        if img_cropped.shape[1] / img_cropped.shape[0] < MIN_PLATE_RATIO or img_cropped.shape[1] / img_cropped.shape[0] > MAX_PLATE_RATIO:
            continue
    
        plate_imgs.append(img_cropped)
        plate_infos.append({
            'x': int(plate_cx - plate_width / 2),
            'y': int(plate_cy - plate_height / 2),
            'w': int(plate_width),
            'h': int(plate_height)
        })
   
    #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
    plt.subplot(len(matched_result), 1, i+1)
    plt.imshow(img_cropped, cmap='gray')
    plt.show()

    #최종 단계
    longest_idx, longest_text = -1, 0
    plate_chars = []

    for i, plate_img in enumerate(plate_imgs):
        plate_img = cv2.resize(plate_img, dsize=(0, 0), fx=1.6, fy=1.6)
    
        #번호판에 대한 전처리, 정확한 문자영역 찾아내기 (threshold, 윤곽선 사각형 이용)
        _, plate_img = cv2.threshold(plate_img, thresh=0.0, maxval=255.0, type=cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    
        contours, _ = cv2.findContours(plate_img, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
    
        plate_min_x, plate_min_y = plate_img.shape[1], plate_img.shape[0]
        plate_max_x, plate_max_y = 0, 0
    
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            #cv2.rectangle(plate_img, pt1=(x, y), pt2=(x+w, y+h), color=(255, 255, 255), thickness=2)
        
            area = w * h
            ratio = w / h

            if area > MIN_AREA \
            and w > MIN_WIDTH and h > MIN_HEIGHT \
            and MIN_RATIO < ratio < MAX_RATIO:
                if x < plate_min_x:
                    plate_min_x = x
                if y < plate_min_y:
                    plate_min_y = y
                if x + w > plate_max_x:
                    plate_max_x = x + w
                if y + h > plate_max_y:
                    plate_max_y = y + h

        '''번호판 사각형 영역 확인
        plt.figure(figsize=(12, 10))
        plt.imshow(plate_img, cmap='gray')
        plt.show()'''
        img_result = plate_img[plate_min_y:plate_max_y, plate_min_x:plate_max_x]
        #ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ중간 결과 확인ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ
        plt.subplot(len(plate_imgs), 1, i+1)
        plt.imshow(img_result, cmap='gray')
        plt.show() ## 문자열만 빼내기
    

        img_result = cv2.copyMakeBorder(img_result, top=10, bottom=10, left=10, right=10, borderType=cv2.BORDER_CONSTANT, value=(0,0,0))

        chars = pytesseract.image_to_string(img_result, lang='kor', config='--psm 7 --oem 0')
    
        result_chars = ''
        has_digit = False
        for c in chars:
            if ord('가') <= ord(c) <= ord('힣') or c.isdigit():
                if c.isdigit():
                    has_digit = True
                result_chars += c
                plate_chars.append(c)
    
        print(result_chars)
        how_car = ''
    
    #차량 차종, 용도 확인
        if len(result_chars) == 7:
            num_f = int(result_chars[:2])
            third_char = result_chars[2]
            
            if 1 <= num_f <= 69:
                how_car+='차종: 승용차 '
            elif 70 <= num_f <= 79:
                how_car+='차종: 승합차 '
            elif 80 <= num_f <= 97:
                how_car+='차종: 화물차 '
            else:
                how_car+='차종: 특수차 '

            if ord('가') <= ord(third_char) <= ord('마') or ord('거') <= ord(third_char) <= ord('저') or ord('고') <= ord(third_char) <= ord('조') or ord('구') <= ord(third_char) <= ord('주'):
                how_car+='용도: 자가용'
            elif ord('바') <= ord(third_char) <= ord('자'):
                how_car+='용도: 사업용(운수)'
            elif ord(third_char) == ord('하') or ord(third_char) == ord('허') or ord(third_char) == ord('호'):
                how_car+='용도: 사업용(렌트카)'
            else:
                how_car+='용도: 사업용(택배)'
    

        elif len(result_chars) == 8:
            num_f = int(result_chars[:3])
            third_char = result_chars[3]
        
        
            if 100 <= num_f <= 699:
                how_car+='차종: 승용차 '
            elif 700 <= num_f <= 799:
                how_car+='차종: 승합차 '
            elif 800 <= num_f <= 979:
                how_car+='차종: 화물차 '
            elif 980 <= num_f <= 997:
                how_car+='차종: 특수차 '
            else:
                how_car+='차종: 긴급차 '

            if ord('가') <= ord(third_char) <= ord('마') or ord('거') <= ord(third_char) <= ord('저') or ord('고') <= ord(third_char) <= ord('조') or ord('구') <= ord(third_char) <= ord('주'):
                how_car+='용도: 자가용'
            elif ord('바') <= ord(third_char) <= ord('자'):
                how_car+='용도: 사업용(운수)'
            elif ord(third_char) == ord('하') or ord(third_char) == ord('허') or ord(third_char) == ord('호'):
                how_car+='용도: 사업용(렌트카)'
            else:
                how_car+='용도: 사업용(택배)'

        print(how_car)
        plt.subplot(len(plate_imgs), 1, i+1)
        plt.imshow(img_result, cmap='gray')
        plt.show()

