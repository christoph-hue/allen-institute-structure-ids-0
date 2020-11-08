! pip install allensdk

from allensdk.api.queries.rma_api import RmaApi
from allensdk.api.cache import Cache
from allensdk.api.queries.grid_data_api  import GridDataApi

import numpy as np
import pandas as pd

# we use the RmaApi to query specific information, such as the section data sets of a specific gene
# for docs, see: https://alleninstitute.github.io/AllenSDK/allensdk.api.queries.rma_api.html
rma = RmaApi() 

# there might be a way to retrieve data in higher resolution, as stated here (default is 25, 10 is also available - but resolution is ignored for download_gene_expression_grid_data)
# https://alleninstitute.github.io/AllenSDK/_modules/allensdk/api/queries/grid_data_api.html
# See `Downloading 3-D Projection Grid Data <http://help.brain-map.org/display/api/Downloading+3-D+Expression+Grid+Data#name="Downloading3-DExpressionGridData-DOWNLOADING3DPROJECTIONGRIDDATA">`_
gdApi = GridDataApi()

# the cache_writeer allows us to easily cache the results
cache_writer = Cache()        

geneAcronym = "Gabra4"
# http://api.brain-map.org/examples/rma_builder/index.html
# http://api.brain-map.org/examples/rma_builder/rma_builder.html
# https://allensdk.readthedocs.io/en/latest/data_api_client.html
sectionDataSets = pd.DataFrame( # wrap is told to be deprecated, but there is no information on what to use instead :(
    cache_writer.wrap(rma.model_query,
                        path='cache\\section-data-sets.json',
                        cache=True, # the semantics of this function are a bit weird. providing True means: add it to the cache
                        model='SectionDataSet',
                        filters={'failed':'false'},
                        include=f"genes[acronym$il{geneAcronym}],products[id$eq1]", # $il = case-insensitive like | yes, weird notation... id = 1 = mouse brain atlas (not developing!)
                        num_rows='all'))
# model's documentation: http://api.brain-map.org/doc/SectionDataSet.html
# https://community.brain-map.org/t/attempting-to-download-substructures-for-coronal-p56-mouse-atlas/174/2

experiments = []
#zipfile.ZipFile(request.urlretrieve(self.url)[0]).read("gridAnnotation.raw")))
# http://help.brain-map.org/display/mousebrain/Documentation
# TODO: i think this is wrong. we have different types of grid data: saggital and coronal. are the annotations in the same order for both??
annotationsU = np.fromfile("annotations/P56_Mouse_gridAnnotation/gridAnnotation.raw", dtype="uint32")
annotations = np.fromfile("annotations/P56_Mouse_gridAnnotation/gridAnnotation.raw", dtype="int32")

# for Mouse P56, structure_graph_id = 1 according to http://help.brain-map.org/display/api/Atlas+Drawings+and+Ontologies
# structure_map = StructureMap(reference_space_key = 'annotation/ccf_2017', resolution=25).get(structure_graph_id=1)

for index, row in sectionDataSets.iterrows(): # https://stackoverflow.com/questions/16476924/how-to-iterate-over-rows-in-a-dataframe-in-pandas
    exp_id = row['id']
    exp_path = f"data/{exp_id}/"

    #refSp = ReferenceSpaceApi()
    #anns = refSp.download_mouse_atlas_volume(age=15, volume_type=GridDataApi.ENERGY, file_name=f'cache\\mouse_atlas_volume.zip')
    #print(anns)

    # http://help.brain-map.org/display/mousebrain/API

    try:
        gdApi.download_gene_expression_grid_data(exp_id, GridDataApi.ENERGY, exp_path)

        expression_levels = np.fromfile(exp_path + "energy.raw",  dtype=np.float32)

        # According to the docs here: http://help.brain-map.org/display/api/Downloading+3-D+Expression+Grid+Data
        # we have "A raw uncompressed float (32-bit) little-endian volume representing average expression energy per voxel. A value of "-1" represents no data. This file is returned by default if the volumes parameter is null."
        # energy = numpy.array(list(struct.iter_unpack("<f", open(exp_path + "energy.raw", "rb").read()))).flatten() # way too complicated, but there is a delta in mean and sum. what is the right value??
        data = pd.DataFrame({"expression_level": expression_levels, "structure_id": annotations})

        # TODO: there is something wrong. some expression_levels are assigned to a structure of id 0. same is true for Jure's approach
        data = data[(data.expression_level != -1)] # (data.structure_id != 0) & ]

        
        print(data[(data.structure_id==0) & (data.expression_level>0)])

    except Exception as e:
        print(f"Error retrieving experiment {exp_id}: {str(e)}")
