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
		background = Helpers.isodata_thresholding(gray)
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
	columns = np.count_nonzero(cleared, axis = 0)
	
	columns[columns<3] = 0
	# print(columns)
	start = 0
	while start < len(columns):
		if columns[start] == 0:
			start += 1
			continue
		if start >= len(columns)-1:
			break
		end = start+1
		while columns[end] > 0:
			end += 1
			if end == len(columns):
				break
		letter = Helpers.remove_black_rows(cleared[:, start:end])
		if is_dash(letter):
			start = end+1
			if start >= len(columns):
				break
			continue
		else:
			if letter.shape[1] >= 3:
				# Helpers.plotImage(letter, cmapType="gray")
				characters.append(letter)
				limits.append((start, end))
		start = end+1
		if start >= len(columns):
				break

	if len(characters) <= 3 or len(characters) >= 9:
		return None, None
	fixed = merge_or_split(characters, limits, cleared, dashes)
	return fixed, dashes


def is_dash(letter):
	rows = np.count_nonzero(letter, axis = 1)
	return len(np.where(rows==0)[0]) >= 1 or np.count_nonzero(letter)>= 0.9*letter.shape[0]*letter.shape[1] or letter.shape[0] <= 1.2*letter.shape[1]
	
	

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
				char = Helpers.remove_black_rows(plate[:, new_lims[0]:new_lims[1]])
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