import os
from random import shuffle, uniform, randint, choice
from copy import deepcopy
from shutil import move
from PIL import Image, ImageEnhance, ImageFilter
from tqdm import tqdm

def get_backgrounds(filepath):
	backgrounds = []
	for file_ in os.listdir(filepath):
		bg = Image.open(f"{filepath}/{file_}").convert("RGB")
		brightness_factor = uniform(0.75, 1.25)
		bg = ImageEnhance.Brightness(bg).enhance(brightness_factor)

		new_size = (int(bg.width * 0.5), int(bg.height * 0.5))
		bg = bg.resize(new_size, Image.LANCZOS)

		backgrounds.append(bg)

	return backgrounds

def get_classes(base_filepath):
	return [folder for folder in os.listdir(base_filepath) if not folder.endswith(".tar.gz")]

def get_random_position(bg_size, sticker_size):
    max_x = bg_size[0] - sticker_size[0]
    max_y = bg_size[1] - sticker_size[1]

    return randint(0, max_x), randint(0, max_y)

def get_images(base_filepath, classes, backgrounds):
	filepaths = []
	counts = []

	for class_ in tqdm(classes):
		folder_filepath = os.path.join(base_filepath, class_)
		image_filepaths = os.listdir(folder_filepath)
		counts.append((class_, len(image_filepaths)))
		shuffle(image_filepaths)

		for image_filepath in image_filepaths:
			full_image_filepath = os.path.join(folder_filepath, image_filepath)

			sticker = Image.open(full_image_filepath).convert("RGB")

			# Brightness
			brightness_factor = uniform(0.75, 1.25)
			sticker = ImageEnhance.Brightness(sticker).enhance(brightness_factor)

			# Scaling
			scale = uniform(0.4, 0.6)
			new_size = (int(sticker.width * scale), int(sticker.height * scale))

			sticker = sticker.resize(new_size, Image.LANCZOS)

			# Feathering
			radius = 10
			diam = 2 * radius
			back = Image.new("RGBA", (sticker.size[0] + diam, sticker.size[1] + diam), (255, 255, 255, 0))
			back.paste(sticker, (radius, radius))

			# Create blur mask
			mask = Image.new("L", (sticker.size[0] + diam, sticker.size[1] + diam), 255)
			paste = Image.new("L", (sticker.size[0] - diam, sticker.size[1] - diam), 0)
			mask.paste(paste, (diam, diam))

			# Blur image and paste blurred edge according to mask
			blur = back.filter(ImageFilter.GaussianBlur(10 / 2))
			back.paste(blur, mask=mask)

			sticker = back

			bg = deepcopy(choice(backgrounds))
			x, y = get_random_position((bg.size[0], bg.size[1]), sticker.size)

			bg.paste(sticker, (x, y), sticker)

			bg = bg.filter(ImageFilter.GaussianBlur)

			x = (x + new_size[0] / 2) / bg.size[0]
			y = (y + new_size[1] / 2) / bg.size[1]
			width = new_size[0] / bg.size[0]
			height = new_size[1] / bg.size[1]

			filepaths.append((class_, full_image_filepath, bg, (x, y, width, height)))
		# 	break
		# break

	return filepaths, counts

def splitting_data(filepaths, counts, splits):
	train = []
	test = []
	val = []

	for count in counts:
		category = count[0]
		total_count = count[1]

		total_train = int(total_count * splits[0])
		total_test = int(total_count * splits[1])
		total_val = total_count - (total_train + total_test)

		train.extend(deepcopy(filepaths[:total_train]))
		del filepaths[:total_train]

		test.extend(deepcopy(filepaths[:total_test]))
		del filepaths[:total_test]

		val.extend(deepcopy(filepaths[:total_val]))
		del filepaths[:total_val]
	
	return train, test, val

def make_folders(filepath):
	if not os.path.exists(filepath):
		print(f"Creating {filepath}...")
		os.mkdir(filepath)

def move_images(dataset, image_folder, label_folder, CLASS_MAP):
	for category, image_filepath_, image, coords in tqdm(dataset):
		filename = image_filepath_[::-1].split("/")[0][4:][::-1]

		textfile_name = filename + ".txt"
		image_name = filename + ".png"

		current_label_filepath = os.path.join(label_folder, textfile_name)

		# Moving synthetic images
		# print(os.path.join(image_folder, image_name))
		image.save(os.path.join(image_folder, image_name))

		# Moving the original images
		# move(image_filepath_, image_folder)

		with open(current_label_filepath, "w+") as f:
			f.write(f"{int(CLASS_MAP[category])} {coords[0]} {coords[1]} {coords[2]} {coords[3]}")

def make_yaml(filepath):
	with open(os.path.join(filepath, "data.yaml"), "w+") as f:
		f.writelines(
			[
				"train: /home/aryam/Desktop/Coding/School/comp_vision/final/data/yolo/images/train\n",
				"val: /home/aryam/Desktop/Coding/School/comp_vision/final/data/yolo/images/val\n\n",
				"nc: 25\n",
				"names: ['CANDY', 'RICE', 'FISH', 'SUGAR', 'BEANS', 'VINEGAR', 'PASTA', 'NUTS', 'JAM', 'CEREAL', 'FLOUR', 'CAKE', 'MILK', 'COFFEE', 'OIL', 'TEA', 'JUICE', 'CHIPS', 'SPICES', 'WATER', 'CHOCOLATE', 'TOMATO_SAUCE', 'SODA', 'CORN', 'HONEY']\n"
			]
		)


CLASS_MAP = {
	"CANDY": 0,
	"RICE": 1,
	"FISH": 2,
	"SUGAR": 3,
	"BEANS": 4,
	"VINEGAR": 5,
	"PASTA": 6,
	"NUTS": 7,
	"JAM": 8,
	"CEREAL": 9,
	"FLOUR": 10,
	"CAKE": 11,
	"MILK": 12,
	"COFFEE": 13,
	"OIL": 14,
	"TEA": 15,
	"JUICE": 16,
	"CHIPS": 17,
	"SPICES": 18,
	"WATER": 19,
	"CHOCOLATE": 20,
	"TOMATO_SAUCE": 21,
	"SODA": 22,
	"CORN": 23,
	"HONEY": 24
}

BACKGROUNDS = get_backgrounds("data/backgrounds")
# print(len(BACKGROUNDS))
# Getting data

base_filepath = "data/non_yolo"
classes = get_classes(base_filepath)
filepaths, counts = get_images(base_filepath, classes, BACKGROUNDS)

# Splitting

# WHILE I RECOGNIZE that there are functions like scikit.train_test_split(), 
# I prefer doing this myself as for each category there aren't many images
# Which might lead to some classes having few to none images

# Total 4947 images
# 80% train
# 5% test
# 15% val

train, test, val = splitting_data(filepaths, counts, [0.8, 0.05, 0.15])
# train, test, val = splitting_data(filepaths, counts, [1, 0, 0])

print(f"Total training samples  : {len(train)}")
print(f"Total testing samples   : {len(test)}")
print(f"Total validation samples: {len(val)}")

# Creating YOLO compatible dataset

# Making folders if they don't exist

base_filepath = "data/yolo"

image_filepath = os.path.join(base_filepath, "images")
image_train = os.path.join(base_filepath, "images/train")
image_val = os.path.join(base_filepath, "images/val")

label_filepath = os.path.join(base_filepath, "labels")
label_train = os.path.join(base_filepath, "labels/train")
label_val = os.path.join(base_filepath, "labels/val")

make_folders(image_filepath)
make_folders(image_train)
make_folders(image_val)

make_folders(label_filepath)
make_folders(label_train)
make_folders(label_val)

# Moving images and creating yaml
make_yaml(base_filepath)

print("training")
move_images(train, image_train, label_train, CLASS_MAP)

print("validation")
move_images(val, image_val, label_val, CLASS_MAP)