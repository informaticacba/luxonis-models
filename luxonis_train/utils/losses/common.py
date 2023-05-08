import torch
import torch.nn as nn
import torch.nn.functional as F

class CrossEntropyLoss(nn.Module):
    def __init__(self, **kwargs):
        super(CrossEntropyLoss, self).__init__()
        self.n_classes = kwargs.get("n_classes")
        loss_dict = kwargs
        loss_dict.pop("n_classes")
        self.criterion = nn.CrossEntropyLoss(
            **loss_dict
        )
    
    def forward(self, preds, labels, **kwargs):
        if labels.ndim == 4:
            # target should be of size (N,...)
            labels = labels.argmax(dim=1) 
        return self.criterion(preds, labels)

class BCEWithLogitsLoss(nn.Module):
    def __init__(self, **kwargs):
        super(BCEWithLogitsLoss, self).__init__()
        self.n_classes = kwargs.get("n_classes")
        loss_dict = kwargs
        loss_dict.pop("n_classes")
        self.criterion = nn.BCEWithLogitsLoss(
            **loss_dict
        )
    
    def forward(self, preds, labels, **kwargs):
        return self.criterion(preds, labels)
    
class FocalLoss(nn.Module):
    # Source: https://www.kaggle.com/code/bigironsphere/loss-function-library-keras-pytorch/notebook
    def __init__(self, alpha=0.8, gamma=2, **kwargs):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, inputs, targets, **kwargs):

        #comment out if your model contains a sigmoid or equivalent activation layer
        inputs = torch.sigmoid(inputs)       
        
        #flatten label and prediction tensors
        inputs = inputs.view(-1).to(torch.float32)
        targets = targets.view(-1).to(torch.float32)

        #first compute binary cross-entropy 
        BCE = F.binary_cross_entropy(inputs, targets, reduction='mean')
        BCE_EXP = torch.exp(-BCE)
        focal_loss = self.alpha * (1-BCE_EXP)**self.gamma * BCE
                       
        return focal_loss
