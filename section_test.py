import argparse
from os.path import join as pjoin

import numpy as np
import torch
import torch.nn.functional as F
from tensorboardX import SummaryWriter

import torchvision.utils as vutils
from core.loader.data_loader import *
from core.metrics import runningScore
from core.utils import np_to_tb
from tqdm import tqdm


def test(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    log_dir, model_name = os.path.split(args.model_path)
    # load model:
    model = torch.load(args.model_path)
    model = model.to(device)  # Send to GPU if available
    writer = SummaryWriter(log_dir=log_dir)

    # class_names = ['upper_ns', 'middle_ns', 'lower_ns',
    #                'rijnland_chalk', 'scruff', 'zechstein']
    class_names = [str(x) for x in range(0,6)]
    running_metrics_overall = runningScore(6)

    splits = ["test1"]
    for sdx, split in enumerate(splits):
        # define indices of the array
        data_test = np.load('data/data_test.npz', allow_pickle=True, mmap_mode='r')
        data_test = data_test['data']
        # print(data_test.shape)
        # data_test = np.transpose(data_test, (1, 2, 0)) # by x 
        data_test = np.transpose(data_test, (2, 1, 0)) # by y
        # print(data_test.shape)
        irange, xrange, depth = data_test.shape

        if args.inline:
            i_list = list(range(irange))
            i_list = ['i_'+str(inline) for inline in i_list]
        else:
            i_list = []

        # if args.crossline:
        #     x_list = list(range(xrange))
        #     x_list = ['x_'+str(crossline) for crossline in x_list]
        # else:
        #     x_list = []
        x_list = [] # no crossline right now

        list_test = i_list + x_list

        file_object = open(
            pjoin('data', 'splits', 'section_' + split + '.txt'), 'w')
        file_object.write('\n'.join(list_test))
        file_object.close()
        print(f"[INFO] Split {split} created.")
        test_set = section_loader(is_transform=True,
                                  split=split,
                                  augmentations=None)
        n_classes = test_set.n_classes

        test_loader = data.DataLoader(test_set,
                                      batch_size=1,
                                      num_workers=0,
                                      shuffle=False)
        counter = 0
        for i, _ in enumerate(test_loader):
            counter+=1
        print("[INFO] Total Sections: ", counter)
        # print the results of this split:
        running_metrics_split = runningScore(n_classes)
        results = []
        # testing mode:
        with torch.no_grad():  # operations inside don't track history
            model.eval()
            total_iteration = 0
            for i, (images, labels) in tqdm(enumerate(test_loader), total=counter):
                total_iteration = total_iteration + 1
                image_original, labels_original = images, labels
                # print(images.shape, labels.shape)
                images, labels = images.to(device), labels.to(device)

                outputs = model(images)

                pred = outputs.detach().max(1)[1].cpu().numpy()
                # print(outputs.shape, pred.shape, pred.T.shape)
                results.append(pred)
                # gt = labels.detach().cpu().numpy()
                # running_metrics_split.update(gt, pred)
                # running_metrics_overall.update(gt, pred)

                # numbers = [0, 99, 149, 399, 499]
                numbers = []

                if i in numbers:
                    tb_original_image = vutils.make_grid(
                        image_original[0][0], normalize=True, scale_each=True)
                    writer.add_image('test/original_image',
                                     tb_original_image, i)

                    labels_original = labels_original.numpy()[0]
                    correct_label_decoded = test_set.decode_segmap(np.squeeze(labels_original))
                    writer.add_image('test/original_label',
                                     np_to_tb(correct_label_decoded), i)
                    out = F.softmax(outputs, dim=1)

                    # this returns the max. channel number:
                    prediction = out.max(1)[1].cpu().numpy()[0]
                    # this returns the confidence:
                    confidence = out.max(1)[0].cpu().detach()[0]
                    tb_confidence = vutils.make_grid(
                        confidence, normalize=True, scale_each=True)

                    decoded = test_set.decode_segmap(np.squeeze(prediction))
                    writer.add_image('test/predicted', np_to_tb(decoded), i)
                    writer.add_image('test/confidence', tb_confidence, i)

                    # uncomment if you want to visualize the different class heatmaps
                    unary = outputs.cpu().detach()
                    unary_max = torch.max(unary)
                    unary_min = torch.min(unary)
                    unary = unary.add((-1*unary_min))
                    unary = unary/(unary_max - unary_min)

                    for channel in range(0, len(class_names)):
                        decoded_channel = unary[0][channel]
                        tb_channel = vutils.make_grid(decoded_channel, normalize=True, scale_each=True)
                        writer.add_image(f'test_classes/_{class_names[channel]}', tb_channel, i)
        # get scores and save in writer()
        # score, class_iou = running_metrics_split.get_scores()
    
    sub = np.transpose(np.array(results), (1, 0, 3, 2))
    print(sub.shape)
    sub = sub[0]
    # sub = np.transpose(sub, (2, 0, 1)) # for x
    sub = np.transpose(sub, (2, 1, 0)) # for y
    sub = sub + 1
    assert sorted(list(np.unique(sub))) == list(range(1,7)), "[ERR] labels wrong"

    np.savez_compressed('submission.npz', prediction = sub)
    writer.close()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Params')
    parser.add_argument('--model_path', nargs='?', type=str, default='path/to/model.pkl',
                        help='Path to the saved model')
    parser.add_argument('--split', nargs='?', type=str, default='test1',
                        help='Choose from: "test1", "test2", or "both" to change which region to test on')
    parser.add_argument('--crossline', nargs='?', type=bool, default=False,
                        help='whether to test in crossline mode')
    parser.add_argument('--inline', nargs='?', type=bool, default=True,
                        help='whether to test inline mode')
    args = parser.parse_args()
    test(args)
