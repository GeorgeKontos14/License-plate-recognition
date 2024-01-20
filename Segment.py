import cv2
import numpy as np
import Helpers

def segment(plate, out=None, binary = False, show=True):
	"""
	Given an image of a plate, it segments eacg character
	"""
	cleared = np.copy(plate)
	if not binary:
		gray = cv2.cvtColor(plate, cv2.COLOR_BGR2GRAY)
		background, _ = Helpers.isodata_thresholding(gray)
		#background, _ = Helpers.adaptive_thresholding(gray, 25, 30) - Does not work well; perhaps try better parameters
		#Helpers.plotImage(background, "Background", cmapType="gray")
		cleared = np.copy(background)
	
	cleared = clear_top_bottom(cleared)
	cleared = dilate_or_erode(cleared)
	if (out):
		cv2.imwrite(out, cleared)
	if show:
		Helpers.plotImage(cleared, cmapType="gray")

	characters = []
	limits = []
	dashes = []
	i = 0
	while i < cleared.shape[1]:
		column = cleared[:, i]
		# Discard columns without enough white pixels
		if np.count_nonzero(column) <= 8:
			i += 1
			continue
		# Find the area of the continuous white pixels
		old_i = i
		while np.count_nonzero(cleared[:, i:i+3]) > 10:
			i += 1
			if i == cleared.shape[1]:
				break
		j = old_i
		if np.count_nonzero(cleared[:, j-3:j]) > 10:
			j = j-3
		letter = cleared[:, j:i]
		
		# Check if the character is a dot or a dash;
		# Dots appear in the beginning of the plates
		# due to shadows. We check by examining how many 
		# of the white pixels are near the middle.
		if is_dash(letter):
			if can_be_dash(len(characters), len(dashes)):
				dashes.append(len(characters))
			continue
		else:
			if letter.shape[1] >= 3:
				characters.append(remove_black_rows(letter))
				limits.append((j, i))
		i += 1
	if len(characters) == 1:
		return None, None
		#return divide_by_8(cleared), dashes
	fixed = merge_or_split(characters, limits, cleared, dashes)
	return fixed, dashes


def is_dash(letter):
	whites = np.count_nonzero(letter)
	middle = int(letter.shape[0]/2)
	upper_mid = middle+int(0.1*letter.shape[0])
	lower_mid = middle-int(0.1*letter.shape[0])
	upper = middle+int(0.2*letter.shape[0])
	lower = middle-int(0.2*letter.shape[0])
	return np.count_nonzero(letter[lower:middle]) > 0.7*whites or np.count_nonzero(letter[lower_mid:upper_mid]) > 0.7*whites or np.count_nonzero(letter[middle:upper]) > 0.7*whites

def clear_top_bottom(binary):
	height, length = binary.shape
	top_black = i = 0
	bottom_black = j = height-1
	left = int(0.05*length)
	right = int(0.95*length)
	result = binary[:, left:right]
	while i < j:
		if np.count_nonzero(result[i]) < 0.05*length:
			top_black = i
		if np.count_nonzero(result[j]) < 0.05*length:
			bottom_black = j
		i += 1
		j -= 1
	return result[top_black:bottom_black]

def merge_or_split(characters, limits, plate, dashes):
	if len(characters) == 6:
		return characters
	copied_chars = characters
	copied_limits = limits
	copied_dashes = dashes
	while len(copied_chars) < 6:
		max_length = 0
		max_length_ind = 0
		for i in range(len(copied_chars)):
			char = copied_chars[i]
			if char.shape[1] > max_length:
				max_length = char.shape[1]
				max_length_ind = i
		mid = int(max_length/2)
		temp = []
		if len(dashes) > 0:
			if copied_dashes[0] == max_length_ind:
				copied_dashes[0] += 1
		if len(dashes) > 1:
			if copied_dashes[1] == max_length_ind:
				copied_dashes[1] += 1
		for i in range(len(copied_chars)):
			if i != max_length_ind:
				temp.append(copied_chars[i])
			else:
				temp.append(copied_chars[i][:, :mid])
				temp.append(copied_chars[i][:, mid:])
		copied_chars = temp

	while len(copied_chars) > 6:
		min_length = plate.shape[1]
		min_length_ind = 0
		for i in range(len(copied_chars)-1):
			if i+1 in copied_dashes:
				continue
			curr_length = copied_chars[i].shape[1] + copied_chars[i+1].shape[1]
			if curr_length < min_length:
				min_length = curr_length
				min_length_ind = i
		temp = []
		temp_lims = []
		if len(dashes) > 0:
			if copied_dashes[0] == min_length_ind+1:
				copied_dashes[0] -= 1
		if len(dashes) > 1:
			if copied_dashes[1] == min_length_ind+1:
				copied_dashes[1] -= 1
		for i in range(len(copied_chars)):
			if i != min_length_ind and i != min_length_ind+1:
				temp.append(copied_chars[i])
				temp_lims.append(copied_limits[i])
			elif i == min_length_ind+1:
				continue
			else:
				new_lims = (copied_limits[i][0], copied_limits[i+1][0])
				temp_lims.append(new_lims)
				char = remove_black_rows(plate[:, new_lims[0]:new_lims[1]])
				temp.append(char)
		copied_chars = temp
		copied_limits = temp_lims		

	return copied_chars

def can_be_dash(chars_length, dashes_length):
	"""
	Returns true if it is possible that the next letter
	detected in the plate can be a dash, according 
	to all the possible formats for the dutch license
	plates.
	"""
	if dashes_length >= 2:
		return False
	if chars_length == 2 and dashes_length == 0:
		return True
	if chars_length == 1 and dashes_length == 0:
		return True
	if chars_length == 3 and dashes_length == 0:
		return True
	if chars_length == 4 and dashes_length == 1:
		return True
	if chars_length == 5 and dashes_length == 1:
		return True
	if chars_length == 3 and dashes_length == 1:
		return True
	return False


def remove_black_rows(letter):
	top = 0
	bottom = letter.shape[0]-1
	while np.count_nonzero(letter[top]) == 0:
		top += 1
	while np.count_nonzero(letter[bottom]) == 0:
		bottom -= 1
	return letter[top:bottom, :]

def dilate_or_erode(plate):
	struct_element = np.array([[0,1,0],
               [1,1,1],
               [0,1,0]], np.uint8)
	ratio = np.count_nonzero(plate)/(plate.shape[1]*plate.shape[0])
	if ratio < 0.261:
		return cv2.erode(cv2.dilate(plate, struct_element), struct_element)
	elif ratio > 0.31:
		return cv2.dilate(cv2.erode(plate, struct_element), struct_element)
	return plate

def divide_by_8(plate):
	chars = []
	length = plate.shape[1]
	step = int(length/8)
	cur = 0
	while len(chars) != 8:
		chars.append(remove_black_rows(plate[:, cur:(cur+step)]))
		cur += step
	return chars