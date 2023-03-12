import torch
import cv2
import numpy as np
from torchvision.utils import draw_bounding_boxes, draw_segmentation_masks, draw_keypoints
import torchvision.transforms.functional as F

from luxonis_train.utils.head_type import *
from luxonis_train.models.heads import *
from luxonis_train.utils.boxutils import xywh2xyxy_coco
from luxonis_train.utils.head_utils import yolov6_out2box


# TODO: find better colormap for colors and put it into torchvision draw functions
def draw_on_image(img, data, head, is_label=False, **kwargs):
    img_shape = head.original_in_shape[2:]

    if isinstance(head.type, Classification) or \
        isinstance(head.type, MultiLabelClassification):
        # TODO: what do we want to visualize in this case? maybe just print predicted class/labels
        return img
    elif isinstance(head.type, SemanticSegmentation):
        if data.ndim == 4:
            data = data[0]
        if is_label:
            masks = data.bool()
        else:
            masks = seg_output_to_bool(data)
        img = draw_segmentation_masks(img, masks, alpha=0.4)
        return img
    elif isinstance(head.type, ObjectDetection):
        label_map = kwargs.get("label_map", None)

        if isinstance(head, YoloV6Head):
            if is_label:
                bboxs = xywh2xyxy_coco(data[:, 2:])
                bboxs[:, 0::2] *= img_shape[1]
                bboxs[:, 1::2] *= img_shape[0]
                labels = data[:,1].int()
            else:
                if "conf_thres" not in kwargs:
                    kwargs["conf_thres"] = 0.3
                if "iou_thres" not in kwargs:
                    kwargs["iou_thres"] = 0.6

                output_nms = yolov6_out2box(data, head, **kwargs)[0]
                bboxs = output_nms[:,:4]
                labels = output_nms[:,5].int()

            if label_map:
                labels_list = [label_map[i] for i in labels]
            
            img = draw_bounding_boxes(img, bboxs, labels=labels_list if label_map else None)
            return img
        
def torch_to_cv2(img, to_rgb=False):
    if img.is_floating_point():
        img = img.mul(255).int()
    img = torch.clamp(img, 0, 255)
    img = np.transpose(img.cpu().numpy().astype(np.uint8), (1, 2, 0))
    if to_rgb:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img

def unnormalize(img, original_mean=(0.485, 0.456, 0.406), 
        original_std=(0.229, 0.224, 0.225), to_uint8=False):
    mean = np.array(original_mean)
    std = np.array(original_std)
    new_mean = -mean/std
    new_std = 1/std
    out_img = F.normalize(img, mean=new_mean,std=new_std)
    if to_uint8:
        out_img = torch.clamp(out_img.mul(255), 0, 255).to(torch.uint8)
    return out_img

def seg_output_to_bool(data):
    masks = torch.empty_like(data, dtype=torch.bool)
    classes = torch.argmax(data, dim=0)
    for i in range(masks.shape[0]):
        masks[i] = classes == i
    return masks
