# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
"""
Run inference on images, videos, directories, streams, etc.

Usage - sources:
    $ python path/to/detect.py --weights yolov5s.pt --source 0              # webcam
                                                             img.jpg        # image
                                                             vid.mp4        # video
                                                             path/          # directory
                                                             path/*.jpg     # glob
                                                             'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                             'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python path/to/detect.py --weights yolov5s.pt                 # PyTorch
                                         yolov5s.torchscript        # TorchScript
                                         yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                         yolov5s.xml                # OpenVINO
                                         yolov5s.engine             # TensorRT
                                         yolov5s.mlmodel            # CoreML (MacOS-only)
                                         yolov5s_saved_model        # TensorFlow SavedModel
                                         yolov5s.pb                 # TensorFlow GraphDef
                                         yolov5s.tflite             # TensorFlow Lite
                                         yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
"""

import argparse
import os
import sys
from pathlib import Path
from time import sleep

import cv2
import torch
import torch.backends.cudnn as cudnn
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
# ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.datasets import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, check_file, check_img_size, check_imshow, check_requirements, colorstr,
                           increment_path, non_max_suppression, print_args, scale_coords, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, time_sync


@torch.no_grad()
def run(save_path=None,    # !!!!!
        show_camera=None,    # !!!!!
        show_text=None,
        my_save_path=None,
        source=ROOT / 'data/images',  # file/dir/URL/glob, 0 for webcam
        weights=ROOT / 'yolov5s.pt',  # model.pt path(s)
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=False,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False  # use OpenCV DNN for ONNX inference
        ):
    my_count = 0
    if my_save_path:
        with open(ROOT / 'global.txt', 'w')as file:
            file.write('1')
            file.close()

    source = str(source)
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.txt') or (is_url and not is_file)
    if is_url and is_file:
        source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    if webcam:
        view_img = check_imshow()
        cudnn.benchmark = True  # set True to speed up constant image size inference
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt)
        bs = len(dataset)  # batch_size
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt)
        bs = 1  # batch_size
    vid_path, vid_writer = [None] * bs, [None] * bs

    # Run inference
    model.warmup(imgsz=(1 if pt else bs, 3, *imgsz))  # warmup
    dt, seen = [0.0, 0.0, 0.0], 0
    for path, im, im0s, vid_cap, s in dataset:
        ttt = '0'   # 0hidden, 1running, 2exit

        t1 = time_sync()
        im = torch.from_numpy(im).to(device)
        im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        if len(im.shape) == 3:
            im = im[None]  # expand for batch dim
        t2 = time_sync()
        dt[0] += t2 - t1

        # Inference
        visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
        pred = model(im, augment=augment, visualize=visualize)
        t3 = time_sync()
        dt[1] += t3 - t2

        # NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
        dt[2] += time_sync() - t3

        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # im.jpg
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0.copy() if save_crop else im0  # for save_crop
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(im.shape[2:], det[:, :4], im0.shape).round()

                # !!!!!
                # Print results
                labels = set()
                dd = {'wooden comb': '可回收物_木质梳子', 'wooden spatula': '可回收物_木质锅铲', 'wooden carving': '可回收物_木雕',
                     'pillow': '可回收物_枕头', 'jelly cup': '可回收物_果冻杯', 'archive bag': '可回收物_档案袋', 'chair': '可回收物_椅子',
                     'mould': '可回收物_模具', 'blanket': '可回收物_毛毯', 'kettle': '可回收物_水壶', 'foam board': '可回收物_泡沫板',
                     'foam box': '可回收物_泡沫盒子', 'fire extinguisher': '可回收物_灭火器', 'lampshade': '可回收物_灯罩',
                     'ashtray': '可回收物_烟灰缸', 'thermos bottle': '可回收物_热水瓶', 'gas stove': '可回收物_燃气灶',
                     'glass products': '可回收物_玻璃制品', 'glassware': '可回收物_玻璃器皿', 'glass pot': '可回收物_玻璃壶',
                     'glass cup': '可回收物_玻璃杯', 'glass ball': '可回收物_玻璃球', 'electric shaver': '可回收物_电动剃须刀',
                     'electric curling stick': '可回收物_电动卷发棒', 'electronic scale': '可回收物_电子秤',
                     'electric blanket': '可回收物_电热毯', 'electric iron': '可回收物_电熨斗', 'electromagnetic furnace': '可回收物_电磁炉',
                     'remote control': '可回收物_电视遥控器', 'circuit board': '可回收物_电路板', 'electric fan': '可回收物_电风扇',
                     'rice cooker': '可回收物_电饭煲', 'boarding pass': '可回收物_登机牌', 'plate': '可回收物_盘子', 'bowl': '可回收物_碗',
                     'tape cartridge': '可回收物_磁带盒', 'magnet': '可回收物_磁铁',
                     'remote control for air conditioner': '可回收物_空调遥控器', 'cage': '可回收物_笼子', 'paper': '可回收物_纸张',
                     'card': '可回收物_卡', 'carton': '可回收物_纸箱', 'paper bag': '可回收物_纸袋', 'can': '可回收物_罐头瓶',
                     'network card': '可回收物_网卡', 'earmuff': '可回收物_耳套', 'hearset': '可回收物_耳机', 'earrings': '可回收物_耳钉耳环',
                     'doll': '可回收物_芭比娃娃', 'tea pot': '可回收物_茶叶罐', 'cake box': '可回收物_蛋糕盒', 'screwdriver': '可回收物_螺丝刀',
                     'coat hanger': '可回收物_衣架', 'Socks': '可回收物_袜子', 'trousers': '可回收物_裤子', 'calculator': '可回收物_计算器',
                     'stapler': '可回收物_订书机', 'microphone': '可回收物_话筒', 'soymilk machine': '可回收物_豆浆机',
                     'router': '可回收物_路由器', 'checkers': '可回收物_跳棋', 'plastic bags': '其他垃圾_PE塑料袋',
                     'paper clip': '其他垃圾_U型回形针', 'disposable cup': '其他垃圾_一次性杯子', 'cotton swab': '其他垃圾_一次性棉签',
                     'bamboo stick': '其他垃圾_串串竹签', 'sticky note': '其他垃圾_便利贴', 'band aid': '其他垃圾_创可贴',
                     'toilet paper': '其他垃圾_卫生纸', 'rubber gloves': '其他垃圾_厨房手套', 'facemask': '其他垃圾_口罩',
                     'album': '其他垃圾_唱片', 'pin': '其他垃圾_图钉', 'desiccant': '其他垃圾_干燥剂', 'foam screen': '其他垃圾_打泡网',
                     'lighter': '其他垃圾_打火机', 'bath towel': '其他垃圾_搓澡巾', 'nut shell': '其他垃圾_果壳', 'towel': '其他垃圾_毛巾',
                     'correction tape': '其他垃圾_涂改带', 'wet tissue': '其他垃圾_湿纸巾', 'cigarette butts': '其他垃圾_烟蒂',
                     'toothbrush': '其他垃圾_牙刷', 'electric mosquito repellent incense': '其他垃圾_电蚊香',
                     'scouring pad': '其他垃圾_百洁布', 'glasses': '其他垃圾_眼镜', 'air conditioning filter': '其他垃圾_空调滤芯',
                     'pen': '其他垃圾_笔', 'pen refill': '其他垃圾_笔芯', 'sticky tape': '其他垃圾_胶带', 'glue packaging': '其他垃圾_胶水废包装',
                     'fly swatter': '其他垃圾_苍蝇拍', 'teapot': '其他垃圾_茶壶', 'straw hat': '其他垃圾_草帽', 'cutting board': '其他垃圾_菜板',
                     'ticket': '其他垃圾_票', 'mouldproof piece': '其他垃圾_防霉防蛀片', 'desiccant bag': '其他垃圾_除湿袋',
                     'napkin': '其他垃圾_餐巾纸', 'food box': '其他垃圾_餐盒', 'pregnancy test kit': '其他垃圾_验孕棒',
                     'feather duster': '其他垃圾_鸡毛掸', 'table tennis racquet': '可回收物_乒乓球拍', 'book': '可回收物_书',
                     'weighing scale': '可回收物_体重秤', 'vacuum cup': '可回收物_保温杯', 'crisper': '可回收物_保鲜盒',
                     'plastic wrap box': '可回收物_保鲜膜带齿盒', 'envelope': '可回收物_信封', 'children toy': '可回收物_儿童玩具',
                     'charging head': '可回收物_充电头', 'charging treasure': '可回收物_充电宝',
                     'rechargeable toothbrush': '可回收物_充电牙刷', 'charging cable': '可回收物_充电线',
                     'eight treasure porridge jar': '可回收物_八宝粥罐', 'stool': '可回收物_凳子', 'knife': '可回收物_刀',
                     'razor blade': '可回收物_剃须刀片', 'scissors': '可回收物_剪刀', 'spoon': '可回收物_勺子', 'fork': '可回收物_叉子',
                     'backpacks': '可回收物_双肩包', 'morphing toys': '可回收物_变形玩具', 'desk calendar': '可回收物_台历',
                     'table lamp': '可回收物_台灯', 'hangtags': '可回收物_吊牌', 'blow dryer': '可回收物_吹风机', 'apron': '可回收物_围裙',
                     'globe': '可回收物_地球仪', 'metro ticket': '可回收物_地铁票', 'cushion': '可回收物_垫子',
                     'plastic buckle': '可回收物_塑料扣', 'plastic cup lid': '可回收物_塑料杯盖', 'plastic bottles': '可回收物_塑料瓶',
                     'plastic basins': '可回收物_塑料盆', 'plastic box': '可回收物_塑料盒', 'milk box': '可回收物_奶盒',
                     'milk powder cans': '可回收物_奶粉罐', 'ruler': '可回收物_尺子', 'nylon rope': '可回收物_尼龙绳',
                     'nylon bag': '可回收物_尼龙袋', 'cloth products': '可回收物_布制品', 'ragdoll': '可回收物_布娃娃', 'hat': '可回收物_帽子',
                     'handbag': '可回收物_手提包', 'cell phone': '可回收物_手机', 'flashlight': '可回收物_手电筒', 'wristwatch': '可回收物_手表',
                     'bracelet': '可回收物_手链', 'packing rope': '可回收物_打包绳', 'packing bags': '可回收物_打包袋',
                     'printer': '可回收物_打印机', 'printer cartridges': '可回收物_打印机墨盒', 'pump': '可回收物_打气筒',
                     'empty bottle of skincare products': '可回收物_护肤品空瓶', 'newspaper': '可回收物_报纸', 'slippers': '可回收物_拖鞋',
                     'plug-in board': '可回收物_插线板', 'washboard': '可回收物_搓衣板', 'radio': '可回收物_收音机',
                     'magnifying glass': '可回收物_放大镜', 'the calendar': '可回收物_日历', 'cans': '可回收物_易拉罐',
                     'hand warmer': '可回收物_暖手宝', 'telescope': '可回收物_望远镜', 'wooden cutting board': '可回收物_木制切菜板',
                     'wooden toys': '可回收物_木制玩具', 'cask': '可回收物_木桶', 'stick': '可回收物_木棍', 'car key': '可回收物_车钥匙',
                     'filter screen': '可回收物_过滤网', 'measuring cup': '可回收物_量杯', 'metal basin': '可回收物_金属盆',
                     'metal disk': '可回收物_金属盘', 'metal bowl': '可回收物_金属碗', 'metal key chain': '可回收物_金属钥匙扣',
                     'nail': '可回收物_钉子', 'iron wire ball': '可回收物_铁丝球', 'aluminum products': '可回收物_铝制用品',
                     'aluminum cover': '可回收物_铝盖', 'pot': '可回收物_锅', 'pot cover': '可回收物_锅盖', 'keyboard': '可回收物_键盘',
                     'tweezers': '可回收物_镊子', 'alarm clock': '可回收物_闹钟', 'umbrella': '可回收物_雨伞', 'coin purse': '可回收物_零钱包',
                     'shoes': '可回收物_鞋', 'sound': '可回收物_音响', 'placemat': '可回收物_餐垫', 'fish bowl': '可回收物_鱼缸',
                     'egg box': '可回收物_鸡蛋包装盒', 'mouse': '可回收物_鼠标', 'health care bottle': '有害垃圾_保健品瓶',
                     'oral liquid bottle': '有害垃圾_口服液瓶', 'cough syrup bottle': '有害垃圾_咳嗽糖浆玻璃瓶', 'nail polish': '有害垃圾_指甲油',
                     'insecticide': '有害垃圾_杀虫剂', 'thermometer': '有害垃圾_温度计', 'eye drop bottle': '有害垃圾_滴眼液瓶',
                     'light bulb': '有害垃圾_灯泡', 'glass tube': '有害垃圾_玻璃灯管', 'physiological saline bottle': '有害垃圾_生理盐水瓶',
                     'battery': '有害垃圾_电池', 'battery panel': '有害垃圾_电池板', 'iodophor bottle': '有害垃圾_碘伏空瓶',
                     'safflower oil': '有害垃圾_红花油', 'button battery': '有害垃圾_纽扣电池', 'glue': '有害垃圾_胶水',
                     'drug packaging': '有害垃圾_药品包装', 'tablet': '有害垃圾_药片', 'ointment': '有害垃圾_药膏',
                     'storage battery': '有害垃圾_蓄电池', 'sphygmomanometer': '有害垃圾_血压计'}

                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string
                    if names[int(c)] not in labels:
                        labels.add(names[int(c)])
                if show_text and labels:
                    string = "可能存在如下垃圾，请及时处理！\n"
                    for nn in labels:
                        string += dd[nn].split('_')[1]
                        string += "，该垃圾应当是："
                        string += dd[nn].split('_')[0]
                        string += '\n'
                    show_text.setText(string)

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                        with open(txt_path + '.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')

                    if save_img or save_crop or view_img:  # Add bbox to image
                        c = int(cls)  # integer class
                        label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                        annotator.box_label(xyxy, label, color=colors(c, True))
                        if save_crop:
                            # !!!!!
                            # save_one_box(xyxy, imc, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)
                            pass

            # Stream results
            im0 = annotator.result()
            file1 = open(ROOT / "save.txt", 'r')
            ttttt = file1.read().strip()
            file1.close()
            if my_save_path and my_save_path[-1] not in ['/', '\\']:
                my_save_path += '/'
            if ttttt == '1' and my_save_path and my_count % 10 == 0:
                string = my_save_path + str(my_count//10).zfill(6) + '.jpg'
                print(' '.join([string, 'saved to', my_save_path]))
                cv2.imwrite(string, im0)
            my_count += 1
            if view_img:
                # cv2.imshow(str(p), im0) # !!!!!
                file1 = open(ROOT / "global.txt", 'r')
                ttt = file1.read().strip()
                file1.close()
                if ttt == '2':
                    return
                    # dataset.cap.release()
                    # cv2.destroyAllWindows()
                    # raise StopIteration
                frame = cv2.cvtColor(im0, cv2.COLOR_BGR2RGB)
                img = QPixmap(QImage(frame, 640, 480, QImage.Format_RGB888))
                # img = img.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                show_camera.setPixmap(img)
                cv2.waitKey(1)  # 1 millisecond

            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if vid_path[i] != save_path:  # new video
                        vid_path[i] = save_path
                        if isinstance(vid_writer[i], cv2.VideoWriter):
                            vid_writer[i].release()  # release previous video writer
                        if vid_cap:  # video
                            fps = vid_cap.get(cv2.CAP_PROP_FPS)
                            w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                            h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        else:  # stream
                            fps, w, h = 30, im0.shape[1], im0.shape[0]
                        save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                        vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    vid_writer[i].write(im0)

        # Print time (inference-only)
        if ttt == '1':
            LOGGER.info(f'{s}Done. ({t3 - t2:.3f}s)')

    # Print results
    t = tuple(x / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
    if update:
        strip_optimizer(weights)  # update model (to fix SourceChangeWarning)
    return save_path    # !!!!!


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolov5s.pt', help='model path(s)')
    parser.add_argument('--source', type=str, default=ROOT / 'data/images', help='file/dir/URL/glob, 0 for webcam')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(FILE.stem, opt)
    return opt


def main(opt):
    check_requirements(exclude=('tensorboard', 'thop'))
    run(**vars(opt))


if __name__ == "__main__":
    opt = parse_opt()
    main(opt)
