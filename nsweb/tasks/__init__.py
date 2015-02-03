from celery import Task
from nsweb.initializers import settings
from neurosynth.base.dataset import Dataset
from neurosynth.analysis import meta
from celery.utils import cached_property
import numpy as np
import pandas as pd
import nibabel as nb
import matplotlib.pyplot as plt
import seaborn as sns
from nilearn.image import resample_img
from nsweb.core import celery
from os.path import join, basename, exists
from nsweb.tasks.scatterplot import scatter
import traceback


def load_image(dataset, filename, save_resampled=True):
    """ Load an image, resampling into MNI space if needed. """
    filename = join(settings.DECODED_IMAGE_DIR, filename)
    img = nb.load(filename)
    if img.shape[:3] != (91, 109, 91):
        img = resample_img(img, target_affine=decode_image.anatomical.get_affine(), 
                            target_shape=(91, 109, 91), interpolation='nearest')
        if save_resampled:
            img.to_filename(filename)
    return dataset.masker.mask(img)

def get_decoder_analysis_data(dd, analysis):
    """ Get analysis's data: check in the decoder DataFrame first, and if not found, 
    read from file (updating the in-memory DF). """
    if analysis not in dd.columns:
            target_file = join(settings.IMAGE_DIR, 'analyses', analysis + '_pFgA_z.nii.gz')
            if not exists(target_file):
                return False
            dd[analysis] = load_image(make_scatterplot.dataset, target_file)
    return dd[analysis].values

class NeurosynthTask(Task):

    @cached_property
    def dataset(self):
        return Dataset.load(settings.PICKLE_DATABASE)

    @cached_property
    def dd(self):  # decoding data
        return pd.read_msgpack(settings.DECODING_DATA)

    @cached_property
    def anatomical(self):
        f = join(settings.IMAGE_DIR, 'anatomical.nii.gz')
        return nb.load(f)

    @cached_property
    def masks(self):
        """ Return a dict of predefined region masks. """
        maps = {
            'cortex': join(settings.MASK_DIR, 'cortex.nii.gz'),
            'subcortex': join(settings.MASK_DIR, 'subcortex_drewUpdated.nii.gz'),
            'hippocampus': join(settings.MASK_DIR, 'FSL_BHipp_thr0.nii.gz'),
            'accumbens': join(settings.MASK_DIR, 'FSL_BNAcc_thr0.nii.gz'),
            'amygdala': join(settings.MASK_DIR, 'FSL_BAmyg_thr0.nii.gz'),
            'putamen': join(settings.MASK_DIR, 'FSL_BPut_thr0.nii.gz'),
            'min4': join(settings.MASK_DIR, 'voxel_counts_r6.nii.gz')
        }
        for m, img in maps.items():
            maps[m] = load_image(self.dataset, img)
        return maps

@celery.task(base=NeurosynthTask)
def count_studies(analysis, threshold=0.001, **kwargs):
    """ Count the number of studies in the Dataset for a given analysis. """
    ids = count_studies.dataset.get_studies(features=str(analysis), frequency_threshold=threshold)
    return len(ids)

@celery.task(base=NeurosynthTask)
def save_uploaded_image(filename, **kwargs):
    pass
    
@celery.task(base=NeurosynthTask)
def decode_image(filename, **kwargs):
    """ Decode a retrieved image. """
    try:
        basefile = basename(filename)
        # Need to fix this--should probably add a "decode_id" field storing a UUID for 
        # any model that needs to be decoded but isn't an upload.
        uuid = 'gene_' + basefile.split('_')[2] if basefile.startswith('gene') else basefile[:32]
        dataset, dd = decode_image.dataset, decode_image.dd
        data = load_image(dataset, filename)

        # For genes, use only subcortical voxels
        if basefile.startswith('gene'):
            subcortex = decode_image.masks['subcortex'].astype(bool)
            data = data[subcortex]
            dd = dd.iloc[subcortex,:]
            
        r = np.corrcoef(data.T, dd.values.T)[0,1:]
        outfile = join(settings.DECODING_RESULTS_DIR, uuid + '.txt')
        pd.Series(r, index=dd.columns).to_csv(outfile, sep='\t')
        return True
    except Exception, e:
        print traceback.format_exc()
        return False

@celery.task(base=NeurosynthTask)
def make_coactivation_map(x, y, z, r=6, min_studies=0.01):
    """ Generate a coactivation map on-the-fly for the given seed voxel. """
    try:
        dataset = make_coactivation_map.dataset
        ids = dataset.get_studies(peaks=[[x, y, z]], r=r)
        if len(ids) < 50: return False
        ma = meta.MetaAnalysis(dataset, ids, min_studies=min_studies)
        outdir = join(settings.IMAGE_DIR, 'coactivation')
        prefix = 'metaanalytic_coactivation_%s_%s_%s' % (str(x), str(y), str(z))
        ma.save_results(outdir, prefix, image_list=['pFgA_z_FDR_0.01'])
        return True
    except Exception, e:
        print traceback.format_exc()
        return False

@celery.task(base=NeurosynthTask)
def make_scatterplot(filename, analysis, base_id, outfile=None, n_voxels=None, allow_nondecoder_analyses=False, 
                    x_lab="Uploaded Image", y_lab=None, gene_masks=False):
    """ Generate a scatter plot displaying relationship between two images (typically a 
        Neurosynth meta-analysis map and a retrieved image), where each voxel is an observation. 
    Args:
        filename (string): the local path to the retrieved image to plot on x axis
        analysis (string): the name of the Neurosynth analysis to plot on y axis
        base_id (string): the UUID to base the output filename on
        outfile (string): if provided, the output file name
        n_voxels (int): if provided, the number of voxels to randomly sample (if None, 
            all voxels are used)
        allow_nondecoder_analyses (boolean): whether to allow non-preloaded analyses 
            (not currently implemented)
        x_lab (string): x axis label
        y_lab (string): y axis label
        gene_masks (boolean): when True, uses predetermined subcortical ROIs as masks; 
            otherwise uses cortex vs. subcortex
    """
    try:
        # Get the data
        x = load_image(make_scatterplot.dataset, filename)
        y = get_decoder_analysis_data(make_scatterplot.dd, analysis)

        # Subsample random voxels
        if n_voxels is not None:
            voxels = np.random.choose(np.arange(len(x)), n_voxels)
            x, y = x[voxels], y[voxels]

        # Set filename if needed
        if outfile is None:
            outfile = join(settings.DECODING_SCATTERPLOTS_DIR, base_id + '_' + analysis + '.png')

        # Generate and save scatterplot
        if y_lab is None:
            y_lab='%s meta-analysis (z-score)' % analysis
        masks = make_scatterplot.masks
        
        if gene_masks:
            spatial_masks = [masks['subcortex']]
            region_labels = ['hippocampus', 'accumbens', 'amygdala', 'putamen']
            voxel_count_mask = masks['min4']
        else:
            spatial_masks = None
            region_labels = ['cortex', 'subcortex']
            voxel_count_mask = None

        region_masks = [masks[l] for l in region_labels]

        scatter(x, y, region_masks=region_masks, mask_labels=region_labels, unlabeled_alpha=0.15,
                        alpha=0.5, fig_size=(12,12), palette='Set1', x_lab=x_lab, 
                        y_lab=y_lab, savefile=outfile, spatial_masks=spatial_masks,
                        voxel_count_mask=voxel_count_mask)

    except Exception, e:
        print e
        print e.message
        return False

@celery.task(base=NeurosynthTask)
def run_metaanalysis(ids, name):
    """ Run a user-defined meta-analysis.
    Args:
        ids (list): list of PMIDs identifying studies to include in the meta-analysis
        name (string): name of the analysis; used in filename of output images
    """
    try:
        ma = meta.MetaAnalysis(run_metaanalysis.dataset, ids)
        outdir = join(settings.IMAGE_DIR, 'analyses')
        ma.save_results(outdir, name, image_list=['pFgA_z_FDR_0.01', 'pAgF_z_FDR_0.01'])
        return True
    except Exception, e:
        return False

