import os
import scipy
import numpy as np
import skimage.io
import skimage.color

import click
from lsun_room import Phase, Dataset
from fcn import fcn32s


def labelcolormap(N=256):

    def bitget(byteval, idx):
        return ((byteval & (1 << idx)) != 0)

    cmap = np.zeros((N, 3))
    for i in range(0, N):
        id = i
        r, g, b = 0, 0, 0
        for j in range(0, 8):
            r = np.bitwise_or(r, (bitget(id, 0) << 7-j))
            g = np.bitwise_or(g, (bitget(id, 1) << 7-j))
            b = np.bitwise_or(b, (bitget(id, 2) << 7-j))
            id = (id >> 3)
        cmap[i, 0] = r
        cmap[i, 1] = g
        cmap[i, 2] = b
    cmap = cmap.astype(np.float32) / 255
    return cmap


phases = {'train': Phase.TRAIN, 'val': Phase.VALIDATE, 'test': Phase.TEST}


@click.command()
@click.argument('weight_path', type=click.Path(exists=True))
@click.option('--phase', type=click.Choice(['train', 'val', 'test']), default='val')  # noqa
def main(weight_path, phase):
    dataset_root = '../data'

    experiment_name = weight_path.split('/')[-2]
    images_folder = 'output_images/%s/' % experiment_name
    layout_folder = 'output_layout/%s/' % experiment_name
    os.makedirs(images_folder, exist_ok=True)
    os.makedirs(layout_folder, exist_ok=True)

    model = fcn32s(weights=weight_path)

    cmap = labelcolormap(5)

    dataset = Dataset(root_dir=dataset_root, phase=phases[phase])
    images = [e.image for e in dataset.items]

    for i, (img, e) in enumerate(zip(images, dataset.items)):
        h, w = 404, 404

        img = scipy.misc.imresize(img, (h, w))

        batched_img = np.expand_dims(img, axis=0)
        pred = model.predict(batched_img)[0, ...]

        pred_img = np.argmax(pred, axis=2)
        out = skimage.color.label2rgb(pred_img, colors=cmap[1:], bg_label=0)

        skimage.io.imsave(images_folder + '%s.png' % e.name, out)
        skimage.io.imsave(layout_folder + '%s.png' % e.name, pred_img)

        print('--> #%d Done' % i, e.name)


if __name__ == '__main__':
    main()
