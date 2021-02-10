import json
from fpdf import FPDF
from PIL import Image, ImageDraw
from io import BytesIO
from round_rect import create_rounded_rectangle_mask

monster_json_path = "gloomhaven-master/data/monster-stat-cards.js"
monster_image_path = "gloomhaven-master/images"
#player_json_path = "gloomhaven-master/data/character-mats.js"
player_json_path = "character-mats.js"
player_image_path = "gloomhaven-master/images"
pdf_base_name = "gloomhaven-tracker"
pdf_playmat = "playmat"

im_crop_monster = (147, 149, 251, 253)  # LURL
im_crop_player = (25, 25, 223, 308)
im_final_size = [2, 2]                  # dimensions [w, h] of final image cards in inches
p_separation = 0.05                     # ratio of image width/height to row/column separation in image arrays
p_margin = 1                            # page margin in inches
p_size = [11, 8.5]                      # Letter

pdf = FPDF(orientation="L", unit="in", format="letter")
image_list = []
with open(monster_json_path) as f:
    monster_json = json.load(f)

    for monster in monster_json:
        if monster['image'][-5:] == "0.png":
            mon_img = Image.open(monster_image_path+"/"+monster['image'])
            image_list.append(mon_img.crop(im_crop_monster))

with open(player_json_path) as f:
    player_json = json.load(f)

    for character in player_json:
        if character['image'][-8:] != "back.png":
            char_img = Image.open(player_image_path+"/"+character['image'])
            image_list.append(char_img.crop(im_crop_player))

'''
Create tracker sheet
'''
pdf.add_page()
tracker_config_json = "Rectangle_Config.json"
rot_matrix = {"RIGHT": 0, "UP": -90, "DOWN": 90, "LEFT": 180}

with open(tracker_config_json) as f:
    tracker_config = json.load(f)

    for element in tracker_config:
        pos = element['pos']
        if element['type'] == 'Text':
            pdf.set_font('helvetica', 'B', element['fontsize'])
            with pdf.rotation(rot_matrix[element['orientation']]):
                pdf.text(pos[0], pos[1], element['body'])

        elif element['type'] == 'Rectangle':
            size = element['size']
            im = Image.new('RGB', [int(size[0]*100), int(size[1]*100)], (0, 0, 0))

            if element['rounded']:
                im = create_rounded_rectangle_mask([int(size[0]*100), int(size[1]*100)],
                                                   int(min(size)*10), element['color'])
            else:
                draw = ImageDraw.Draw(im)
                draw.rectangle((0, 0, size[0]*100, size[1]*100), element['color'], element['border'])

            with BytesIO() as im_cache:
                im.save(im_cache, format="PNG")
                pdf.image(im_cache, pos[0], pos[1], size[0], size[1])

        else:
            print("unknown type: {}".format(element[type]))



'''
Write out the monster cards to pdf
'''
pdf.add_page()
pdf.set_font('helvetica', 'B', 16)

x_max = p_size[0] - p_margin - im_final_size[0]
y_max = p_size[1] - p_margin - im_final_size[1]

row_count = 0
col_count = 0
ind = 0
while ind < len(image_list):
    x_pos = p_margin + im_final_size[0]*col_count*(1+p_separation)
    y_pos = p_margin + im_final_size[1]*row_count*(1+p_separation)
    if x_pos > x_max:  # new row
        row_count += 1
        col_count = 0
    elif y_pos > y_max:  # new page
        pdf.add_page()
        row_count = 0
        col_count = 0
    else:
        with BytesIO() as im_cache:
            image_list[ind].save(im_cache, format="PNG")
            pdf.image(im_cache, x_pos, y_pos, im_final_size[0], im_final_size[1])
        # add name (vertical, right of image)
        # draw box around image and name
        col_count += 1
        ind += 1


pdf.output(pdf_base_name+".pdf", "F")
