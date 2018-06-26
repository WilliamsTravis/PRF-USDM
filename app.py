# In[]:
################################# Switching to/from Ubuntu VPS ##############################################################
from sys import platform
import os

if platform == 'win32':
    homepath = "C:/users/user/github/PRF-USDM"
    os.chdir(homepath)
else:
    homepath = "/home/ubuntu/PRF-USDM"
    os.chdir(homepath)

#os.chdir("/var/www/FlaskApp/FlaskApp")
from functions import *
# Empty Slice Warnings are  numerous and meaningless
import warnings
warnings.filterwarnings("ignore") 

############################ Get Data #########################################
source = xr.open_dataarray("data/source_array.nc")
source_signal = '["data//rainfall_indices.npz", 4, 0.7,100]'
grid = np.load("data/prfgrid.npz")["grid"]
states = np.load("data/states.npz")["states"]
mask = np.load("data/mask.npz")['mask']
statefps = pd.read_csv("data/statefps.csv")

# Load pre-conditioned bi-monthly USDM modal category rasters into numpy arrays
with np.load("data/usdm_arrays.npz") as data:
    usdmodes = data.f.arr_0
    data.close()
with np.load("data/usdm_dates.npz") as data:
    udates = data.f.arr_0
    data.close()
usdmodes = [[str(udates[i]),usdmodes[i]] for i in range(len(usdmodes))]

###############################################################################
############################ Create the App Object ############################
###############################################################################
# Create Dash Application Object
app = dash.Dash(__name__)

# I really need to get my own stylesheet, if anyone know how to do this...
app.css.append_css({'external_url': 'https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'})  # noqa: E501

# Create server object
server = app.server

# Create and initialize a cache for storing data - data pocket
#cache = Cache(config = {'CACHE_TYPE':'simple'})
#cache.init_app(server)

###############################################################################
############################ Create Lists and Dictionaries ####################
###############################################################################
# Index Paths
indices = [{'label':'Rainfall Index','value':'data/rainfall_indices.npz'}
#           {'label':'PDSI','value':'D:\\data\\droughtindices\\palmer\\pdsi\\nad83\\'},
#           {'label':'PDSI-Self Calibrated','value':'D:\\data\\droughtindices\\palmer\\pdsisc\\nad83\\'},
#           {'label':'Palmer Z Index','value':'D:\\data\\droughtindices\\palmer\\pdsiz\\nad83\\'},
#           {'label':'EDDI-1','value':'D:\\data\\droughtindices\\eddi\\nad83\\monthly\\1month\\'},
#           {'label':'EDDI-2','value': 'D:\\data\\droughtindices\\eddi\\nad83\\monthly\\2month\\'},
#           {'label':'EDDI-3','value':'D:\\data\\droughtindices\\eddi\\nad83\\monthly\\3month\\'},
#           {'label':'EDDI-6','value':'D:\\data\\droughtindices\\eddi\\nad83\\monthly\\6month\\'},
#           {'label':'SPI-1' ,'value': 'D:\\data\\droughtindices\\spi\\nad83\\1month\\'},
#           {'label':'SPI-2' ,'value': 'D:\\data\\droughtindices\\spi\\nad83\\2month\\'},
#           {'label':'SPI-3' ,'value': 'D:\\data\\droughtindices\\spi\\nad83\\3month\\'},
#           {'label':'SPI-6' ,'value': 'D:\\data\\droughtindices\\spi\\nad83\\6month\\'},
#           {'label':'SPEI-1' ,'value': 'D:\\data\\droughtindices\\spei\\nad83\\1month\\'},
#           {'label':'SPEI-2' ,'value': 'D:\\data\\droughtindices\\spei\\nad83\\2month\\'},
#           {'label':'SPEI-3' ,'value': 'D:\\data\\droughtindices\\spei\\nad83\\3month\\'},
#           {'label':'SPEI-6','value': 'D:\\data\\droughtindices\\spei\\nad83\\6month\\'}
           ]

# Index names, using the paths we already have. These are for titles.
indexnames = {'data/rainfall_indices.npz': 'Rainfall Index'}
#            'D:\\data\\droughtindices\\palmer\\pdsi\\nad83\\': 'Palmer Drought Severity Index',
#            'D:\\data\\droughtindices\\palmer\\pdsisc\\nad83\\': 'Self-Calibrated Palmer Drought Severity Index',
#            'D:\\data\\droughtindices\\palmer\\pdsiz\\nad83\\': 'Palmer Z Index',
#            'D:\\data\\droughtindices\\eddi\\nad83\\monthly\\1month\\':'Evaporative Demand Drought Index - 1 month',
#            'D:\\data\\droughtindices\\eddi\\nad83\\monthly\\2month\\':'Evaporative Demand Drought Index - 2 month',
#            'D:\\data\\droughtindices\\eddi\\nad83\\monthly\\3month\\':'Evaporative Demand Drought Index - 3 month',
#            'D:\\data\\droughtindices\\eddi\\nad83\\monthly\\6month\\':'Evaporative Demand Drought Index - 6 month',
#            'D:\\data\\droughtindices\\spi\\nad83\\1month\\':'Standardized Precipitation Index - 1 month',
#            'D:\\data\\droughtindices\\spi\\nad83\\2month\\':'Standardized Precipitation Index - 2 month',
#            'D:\\data\\droughtindices\\spi\\nad83\\3month\\':'Standardized Precipitation Index - 3 month',
#            'D:\\data\\droughtindices\\spi\\nad83\\6month\\':'Standardized Precipitation Index - 6 month',
#            'D:\\data\\droughtindices\\spei\\nad83\\1month\\': 'Standardized Precipitation-Evapotranspiration Index - 1 month', 
#            'D:\\data\\droughtindices\\spei\\nad83\\2month\\': 'Standardized Precipitation-Evapotranspiration Index - 2 month', 
#            'D:\\data\\droughtindices\\spei\\nad83\\3month\\': 'Standardized Precipitation-Evapotranspiration Index - 3 month', 
#            'D:\\data\\droughtindices\\spei\\nad83\\6month\\': 'Standardized Precipitation-Evapotranspiration Index - 6 month'
#            }

# State options
statefps = statefps.sort_values('state')
statefps = statefps.reset_index()
stateoptions = [{'label':statefps['state'][i],'value':statefps['statefp'][i]} for i in range(len(statefps['state']))]
stateoptions.insert(0,{'label':'All','value':100})
stateoptions.remove({'label':'District of Columbia','value':8})

# Data Summary
datatable = pd.read_csv("data/state_risks.csv",index_col=0)
datatable = datatable.dropna()
datatable = datatable[datatable.State != 'District of Columbia'].to_dict('RECORDS')

columnkey = [{'label':'Strike Level:            Rainfall Index Strike Level','value': 1},
             {'label':'DM Category:             Drought Monitor Drought Severity Category','value': 2},
             {'label':'Missed (sum):            Total Number of times the rainfall index would not have paid given the chosen US Drought Monitor Severity Category','value': 3},
             {'label':'Missed (ratio):          Ratio between the number of times the USDM reached the chosen drought category and the numbers of time rainfall index would not have paid','value': 4},
             {'label':'Strike Events:           Number of times the rainfall index fell below the strike level','value': 5},
             {'label':'DM  Events:              Number of times the USDM reached the chosen category','value': 6}]


# Strike levels
strikes = [{'label':'70%','value':.70},
          {'label':'75%','value':.75},
          {'label':'80%','value':.80},
          {'label':'85%','value':.85},
          {'label':'90%','value':.90}]

DMs = [{'label':'D4','value':4},
       {'label':'D3','value':3},
       {'label':'D2','value':2},
       {'label':'D1','value':1},
       {'label':'D0','value':0}]


DMlabels = {0:'D0',
            1:'D1',
            2:'D2',
            3:'D3',
            4:'D4'}

## Create Coordinate Index - because I can't find the array position in the
    # click event!
xs = range(300)
ys = range(120)
lons = [-130 + .25*x for x in range(0,300)]
lats = [49.75 - .25*x for x in range(0,120)]
londict = dict(zip(lons, xs))
latdict = dict(zip(lats, ys))
londict2  = {y:x for x,y in londict.items()} # This is backwards to link simplified column
latdict2  = {y:x for x,y in latdict.items()} # This is backwards to link simplified column

######################### Total Project Description #########################################################################
# Descriptions
raininfo = "The number of times the rainfall index fell below the chosen strike level."
dminfo = "The number of times the Drought Monitor reached the chosen drought severity category."
countinfo = "The number of times the Drought Monitor reached or exceeded the chosen drought severity category and the rainfall index did not fall below the chosen strike level."
ratioinfo = "The ratio between the number of times the rainfall index at the chosen strike level would not have paid during a drought according to the chosen USDM category and the number of times that the USDM category was met or exceeded. Only locations with 10 or more drought events are included."
#description= open("README.txt").read() # Does anyone know how justify a text file for RMarkdown?
description = ''
description_text = '''

##### Quantifying Pasture, Rangeland, and Forage Insurance Basis Risk using the United States Drought Monitor

Weather-based index insurance is a relatively novel  type of plan  whereby payouts are  based on  an  independent  indicator of  loss, rather than  on direct measurements. The 
index quantifies deviations from a baseline average value for a specific location and indemnifies when an observed value falls below a certain percentage of this normal value.
Such  products are useful  where there is  no  readily  available measurement of direct  loss, or where problems of moral hazard and adverse  selection preclude  a traditional 
loss-based insurance design. Cumulative rainfall  is  often used as the basis for  loss in weather-based index insurance  programs. It  is most often  used in  scenarios where 
rainfall is assumed to correlate well with an  agricultural commodity such as  grain crop yields,  hay, or rangeland  forage production.  Many studies, though, have found that 
simple  cumulative  rainfall is poorly correlated  with  plant  production which  also depends on  additional factors such as patterns of rainfall and evapotranspiration while 
uptake  is  relatively low  for the  same  reason. This  discrepancy is  common in weather-based index  insurance and is generally referred to as basis risk. Basis risk can be 
quantified if a tertiar measure of loss is employed,  ideally  a sample of  direct measurements, though  where this  is not available  alternative metrics can be  established.
In Muneepeerakul et al  (2017)  researchers quantify the  basis risk involved with cumulative rainfall insurance for corn producers using a calculated measure of minimum yield 
required to “break-even” based on production costs and commodity price. Basis risk here is defined as the probability that the rainfall index does not fall below a  percentage 
of normal (strike), and fails to indemnify, when the revenue metric indicates yields below the chosen threshold. This can be expressed as, **Basis Risk = P[ RF > RF_strike |  Y  <  Y_strike]**
Where RF is the observed rainfall index value, RF_strike is the level of rainfall that  triggers payout, Y is the observed yield and Y_strike is the yield needed to recover 
production expenses. The Pasture Rangeland and Forage insurance program (PRF)  of the USDA’s Risk Management Agency uses a rainfall index to compensate policyholders for added 
feed and operation costs resulting  from grazing and  haying shortages due of drought.  Here, we apply the same approach as Muneepeerakul et al (2017) to  quantify the risk of 
non-indemnification given loss. We do  not, however, have the access to any sort of  yield data for this industry as would be  available for grain  production.  Instead we are 
using the United States Drought Monitor (USDM)  which is referred to as the “standard  operational drought  monitor for the  United States”   and  commonly used by ranchers to 
inform  management  strategies. We  decided that the  USDM  is a viable  option for  the quantification of basis  risk both because we are assuming it to better correlate with 
grassland impacts due to drought and because of its utility and familiarity to rangeland managers. 
The PRF allows policyholders  to select from a  set of optional  payment threshold  levels: 70, 75,  80, 85, and 90% of average rainfall. Insurance periods are binned into 
overlapping bi-monthly intervals; January to February, February to March, etc. The USDM categorizes drought by increasing levels of severity which is informed by drought index 
values, such as  the Palmer Drought Severity Index, and expert assessments of local professionals.These categories range from mild drought (D0) to exceptional drought (D4) and
are updated weekly.  A gridded variety of the USDM was created to  associate drought  categories to the grid cell  system that the PRF uses  to associate rainfall with  policy 
locations. Because the  rainfall index is based on rainfall data average over  bi-monthly intervals, this USDM was created to reflect drought conditions over that same span of 
time. Because it is  categorical, each bimonthly  period was associated with  the modal drought severity category of the 8 values reported for each grid cell. This potentially 
excludes the influence of possible spikes in drought severity, but this method  is simple and easy to explain and is expected to generally reflect  accumulated drought impacts 
given the slow and gradual nature of drought.
To calculate basis risk,  we assume that  the five threshold  levels in the PRF  correspond to the 5 levels of  drought  severity in the USDM, such that, for any location,
**Basis Risk = P[ RF > RF_strike    |  USDM > USDM_strike]**, where RF is a vector PRF rainfall index values, RFstrike is one of the five threshold payment levels, USDM is a corresponding vector of observed USDM category, and USDM_strike 
is the USDM level that is assumed to correspond RFstrike. Therefore, basis risk is defined as the probability, for a given location, that the PRF will not payout when the USDM
indicates a drought. 

Earth Lab – CIRES at the University of Colorado Boulder;
Author: Travis Williams; 
Email: Travis.Williams@colorado.edu; 
Date: 5-26-2018

'''
# Create global chart template
mapbox_access_token = 'pk.eyJ1IjoidHJhdmlzc2l1cyIsImEiOiJjamZiaHh4b28waXNkMnptaWlwcHZvdzdoIn0.9pxpgXxyyhM6qEF_dcyjIQ'

# Map Layout:
layout = dict(
    autosize=True,
    height=500,
    font=dict(color='#CCCCCC'),
    titlefont=dict(color='#CCCCCC', size='20'),
    margin=dict(
        l=10,
        r=10,
        b=35,
        t=55
    ),
    hovermode="closest",
    plot_bgcolor="#191A1A",
    paper_bgcolor="#020202",
    legend=dict(font=dict(size=10), orientation='h'),
    title='Potential Payout Frequencies',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="dark",
        center=dict(
            lon= -95.7,
            lat= 37.1
        ),
        zoom=3,
    )
)


# In[]:
# Create app layout
app.layout = html.Div(
    [   html.Div(# Pictures
            [
                # Title and Image
                html.A(html.Img(
                    src = "https://github.com/WilliamsTravis/Pasture-Rangeland-Forage/blob/master/data/earthlab.png?raw=true",
                    className='one columns',
                    style={
                        'height': '40',
                        'width': '100',
                        'float': 'right',
                        'position': 'static'
                        },
                            ),
                        href = "https://www.colorado.edu/earthlab/",
                        target = "_blank"
                        ),
                html.A(html.Img(
                    src = "https://github.com/WilliamsTravis/Pasture-Rangeland-Forage/blob/master/data/wwa_logo2015.png?raw=true",
                    className='one columns',
                    style={
                        'height': '50',
                        'width': '150',
                        'float': 'right',
                        'position': 'static',
                        },
                            ),
                        href = "http://wwa.colorado.edu/",
                        target = "_blank"
                            ),
                 html.A(html.Img(
                    src = "https://github.com/WilliamsTravis/Pasture-Rangeland-Forage/blob/master/data/nidis.png?raw=true",
                    className='one columns',
                    style={
                        'height': '50',
                        'width': '200',
                        'float': 'right',
                        'position': 'relative',
                        },
                            ),
                        href = "https://www.drought.gov/drought/",
                        target = "_blank"
                        ),
                 html.A(html.Img(
                    src = "https://github.com/WilliamsTravis/Pasture-Rangeland-Forage/blob/master/data/cires.png?raw=true",
                    className='one columns',
                    style={
                        'height': '50',
                        'width': '100',
                        'float': 'right',
                        'position': 'relative',
                        'margin-right':'20',
                        },
                            ),
                        href = "https://cires.colorado.edu/",
                        target = "_blank"
                        ),

                    ],
                    className = "row",

            ),
        html.Div(# Title
            [
                html.H1(
                    'Pasture, Rangeland, and Forage Insurance and the US Drought Monitor: Risk of Non-Payment During Drought',
                    className='twelve columns',
                ),
                html.Button(id = 'description_button',
                     children = 'Project Description (Click)',
                     #title = description,
                     type='button'),
            ],
            className='row',
            style = {
                    'font-weight':'bold',
                     'text-align':'center',
                     'margin-top':'40',
                     'margin-bottom':'40'
                     },
        ),
        html.Div([

                html.Div(
                [
                    dcc.Markdown(id = "description",
                                children = description)
                ],
                style = {
                         'text-align':'justify',
                         'margin-left':'150',
                         'margin-right':'150',
                         'position':'center'
                         }
                ),
                ],
),

        html.Div(# Four
            [
                html.Div(# Four-a
                    [
                        html.P('Drought Index'),
                        dcc.Dropdown(
                            id = 'index_choice',
                            options = indices,
                            multi = False,
                            placeholder = "Rainfall Index",
                            value = "data/rainfall_arrays.npz"
                        ),
                        html.P("Filter by State"),
                        dcc.Dropdown(
                                id = "state_choice",
                                options = stateoptions,
                                value = 100,
                                multi = True,
                                searchable = True
                                ),
                        html.Button(id='submit', type='submit', n_clicks = 0, children='submit')
                    ],
                    className='six columns',
                    style = {'margin-top':'20'},
                ),
                html.Div(# Four-a
                    [
                        html.P('RMA Strike Level'),
                        dcc.RadioItems(
                            id='strike_level',
                            options=strikes,
                            value=.85,
                            labelStyle={'display': 'inline-block'}
                        ),
                        html.P('USDM Category'),
                        dcc.RadioItems(
                            id='usdm_level',
                            options=DMs,
                            value=1,
                            labelStyle={'display': 'inline-block'}
                        ),
                    ],
                    className='six columns',
                    style = {'margin-top':'20'},

                ),
               ],
                className = 'row'
            ),
        html.Div(#Six
            [
                html.Div(#Six-a
                    [
                        dcc.Graph(id='rain_graph'),
                        html.Button(title = raininfo,
                                    type='button',
                                    children='Map Info \uFE56 (Hover)'),
                    ],
                    className='six columns',
                    style={'margin-top': '10'}
                ),
                html.Div(#Six-a
                    [
                        dcc.Graph(id='drought_graph'),
                        html.Button(title = dminfo,
                                    type='button',
                                    children='Map Info \uFE56 (Hover)'),
                    ],
                    className='six columns',
                    style={'margin-top': '10'}
                ),
            ],
            className='row'
        ),
        html.Div(#Six
            [
                html.Div(#Six-a
                    [
                        dcc.Graph(id='hit_graph'),
                        html.Button(title = countinfo,
                                    type='button',
                                    children='Map Info \uFE56 (Hover)'),
                    ],
                    className='six columns',
                    style={'margin-top': '10'}
                ),
                html.Div(#Six-a
                    [
                        dcc.Graph(id='basis_graph'),
                        html.Button(title = ratioinfo,
                                    type='button',
                                    children='Map Info \uFE56 (Hover)'),
                    ],
                    className='six columns',
                    style={'margin-top': '10'}
                ),
            ],
            className='row'
        ),
        # Data Table
         html.Div(#Seven
            [
                html.Div(
                    [   html.H1(" "),
                        html.H4('Summary Statistics'),
                        html.H5("Column Key"),
                        dcc.Dropdown(options = columnkey,
                                     placeholder = "Column Name: Description"),
                        dt.DataTable(
                             rows = datatable,
                             id = "summary_table",
                             editable=False,
                             filterable=True,
                             sortable=True,
                             row_selectable=True,
#                             min_width = 1655,
                             )
                    ],
                    className='twelve columns',
                    style={'width':'100%',
                           'display': 'inline-block', 
                           'padding': '0 20'},
                ),
            ],
            className='row'
        ),
        html.Div(id='signal', style={'display': 'none'})
    ],
    className='ten columns offset-by-one'
)

# In[]:
###############################################################################
######################### Create Cache ########################################
###############################################################################
#@cache.memoize()
def global_store(signal):
    # Transform the argument list back to normal
#    if not signal:
#        signal = source_signal
    signal = json.loads(signal)

    # Unpack signals
    index_choice = signal[0]
    usdm_level = signal[1]
    strike_level = signal[2]
    statefilter = signal[3]
    if type(statefilter) != list:
        statefilter2 = []
        statefilter2.append(statefilter)
        statefilter = statefilter2
    ## Get the index to compare to usdm - later there will be many choices
    # Load Rainfall Index
    with np.load("data/rainfall_indices.npz") as data:
        indexlist = data.f.arr_0
        data.close()
    with np.load("data/rainfall_dates.npz") as data:
        rdates = data.f.arr_0
        data.close()
    indexlist = [[str(rdates[i]),indexlist[i]] for i in range(len(indexlist))]

    # Now, to check both against each other, but first, match times
    udates = [m[0][-6:] for m in usdmodes]
    indexlist = [i for i in indexlist if i[0][-6:] in udates]
    idates = [m[0][-6:] for m in indexlist]
    usdms = [u for u in usdmodes if u[0][-6:] in idates]

    # Create a list of monthly arrays with 1's for the scenario
    risks = [basisCheck(usdm = usdms[i],noaa = indexlist[i],
                        strike = strike_level, dm = usdm_level) for i in range(len(usdms))]

    # Sum them up
    hits = np.nansum(risks,axis = 0)*mask

    # Create a list of monthly arrays with 1's for droughts
    droughts = [droughtCheck(usdm = usdmodes[i],dm = usdm_level) for i in range(len(usdmodes))]
    rainbelow = [droughtCheck2(rain = indexlist[i],strike = strike_level) for i in range(len(indexlist))]

    # Sum and divide by time steps
    droughtchances = np.nansum(droughts,axis = 0)*mask
    rainchance = np.nansum(rainbelow,axis = 0)*mask

    # Final Basis risk according to the USDM and Muneepeerakul et als method
    basisrisk = hits/droughtchances

    # Possible threshold for inclusion
    # select only those cells with 10 or more dm events
    threshold = np.copy(droughtchances)
    threshold[threshold<10] = np.nan
    threshold = threshold*0+1
    basisrisk = basisrisk * threshold
#     Filter if a state or states were selected
    if str(type(statefilter)) + str(statefilter) == "<class 'list'>[100]":
        statemask = np.copy(states)
        statemask = statemask*0+1
        typeof = str(type(statefilter)) + str(statefilter)

    elif "," not in str(statefilter):
        statemask = np.copy(states)
        statelocs = np.where(statemask ==  statefilter)
        statemask[statelocs] = 999
        statemask[statemask < 999] = np.nan
        statemask = statemask*0+1
        typeof = str(type(statefilter)) + str(statefilter)
    else:
        statemask = np.copy(states)
        statelocs = [np.where(statemask==f) for f in statefilter]
        statelocs1 = np.concatenate([statelocs[i][0]for i in range(len(statelocs))])
        statelocs2 = np.concatenate([statelocs[i][1] for i in range(len(statelocs))])
        statelocs = [statelocs1,statelocs2]
        statemask[statelocs] = 999
        statemask[statemask < 999] = np.nan
        statemask = statemask*0+1
        typeof = str(type(statefilter)) + str(statefilter)

    # Package Returns for later
    df = [basisrisk*statemask, droughtchances*statemask,hits*statemask,rainchance*statemask]

    return df

def retrieve_data(signal):
    df = global_store(signal)
    return df

# Store the data in the cache and hide the signal to activate it in the hidden div
@app.callback(Output('signal', 'children'),
              [Input('submit','n_clicks')],
              [State('index_choice','value'),
               State('usdm_level','value'),
               State('strike_level','value'),
               State('state_choice','value')])
def compute_value(click,index_choice,usdm_level,strike_level,state_choice):
    # Package the function arguments
    signal = json.dumps([index_choice,usdm_level,strike_level,state_choice])
    # compute value and send a signal when done
    global_store(signal)
    return signal

@app.callback(Output('description', 'children'),
              [Input('description_button', 'n_clicks')])
def toggleDescription(click):
    if not click:
        click = 0
    if click%2 == 1:
        description = description_text
    else:
        description = ""
    return description

# In[]:
###############################################################################
######################### Graph Builders ######################################
###############################################################################
@app.callback(Output('rain_graph', 'figure'),
              [Input('signal','children')])
def rainGraph(signal):
    # Get data
    if not signal:
        signal = source_signal
    df = retrieve_data(signal)
    # Transform the argument list back to normal
    signal = json.loads(signal)

    # Unpack signals
    index_choice = signal[0]
    usdm_level = signal[1]
    strike_level = signal[2]


    # Get desired array
    payouts = df[3]

    # Second, convert data back into an array, but in a from xarray recognizes
    array = np.array([payouts],dtype = "float32")

    # Third, change the source array to this one. Source is defined up top
    source.data = array

    # Fourth, bin the values into lat, long points for the dataframe
    dfs = xr.DataArray(source, name = "data")
    pdf = dfs.to_dataframe()
    step = .25
    to_bin = lambda x: np.floor(x / step) * step
#    pdf['data'] = pdf['data'].fillna(999)
#    pdf['data'] = pdf['data'].astype(int)
#    pdf['data'] = pdf['data'].astype(str)
#    pdf['data'] = pdf['data'].replace('-1', np.nan)
    pdf["latbin"] = pdf.index.get_level_values('y').map(to_bin)
    pdf["lonbin"] = pdf.index.get_level_values('x').map(to_bin)
    pdf['gridx']= pdf['lonbin'].map(londict)
    pdf['gridy']= pdf['latbin'].map(latdict)
    grid2 = np.copy(grid)
    grid2[np.isnan(grid2)] = 0
    pdf['grid'] = grid2[pdf['gridy'],pdf['gridx']]
    pdf['grid'] = pdf['grid'].apply(int).apply(str)
    pdf['data'] = pdf['data'].astype(float).round(3)
    pdf['printdata'] = "GRID #: " + pdf['grid'] +"<br>Data: " + pdf['data'].apply(str)
    groups = pdf.groupby(("latbin", "lonbin"))
    df_flat = pdf.drop_duplicates(subset=['latbin', 'lonbin'])
    df = df_flat[np.isfinite(df_flat['data'])]

     # Add Grid IDs
    colorscale = [[0, 'rgb(2, 0, 68)'], [0.35, 'rgb(17, 123, 215)'],# Make darker (pretty sure this one)
                    [0.45, 'rgb(37, 180, 167)'], [0.55, 'rgb(134, 191, 118)'],
                    [0.7, 'rgb(249, 210, 41)'], [1.0, 'rgb(255, 249, 0)']] # Make darker

# Create the scattermapbox object
    data = [
        dict(
        type = 'scattermapbox',
#        locationmode = 'USA-states',
        lon = df['lonbin'],
        lat = df['latbin'],
        text = df['printdata'],
        mode = 'markers',
        marker = dict(
            colorscale = colorscale,
            cmin = 0,
            color = df['data'],
            cmax = df['data'].max(),
            opacity=0.85,
            colorbar=dict(
                title= "Frequency<br>(out of 199)",
                textposition = "auto",
                orientation = "h"
                )
            )
        )]
    
    layout['title'] = " Rainfall Index | Sub " + str(int(strike_level*100)) + "% Frequency"
    layout['mapbox']['zoom'] = 2
    # Seventh wrap the data and layout into one
    figure = dict(data=data, layout=layout)
#    return {'figure':figure,'info': index_package_all}
    return figure

# In[]:
@app.callback(Output('drought_graph', 'figure'),
              [Input('signal','children')])
def droughtGraph(signal):

    # Get data
    df = retrieve_data(signal)

    # Transform the argument list back to normal
    signal = json.loads(signal)

    # Unpack signals
    index_choice = signal[0]
    usdm_level = signal[1]
    strike_level = signal[2]


    # Get desired array
    droughtchances = df[1]

    # Second, convert data back into an array, but in a from xarray recognizes
    array = np.array([droughtchances],dtype = "float32")

    # Third, change the source array to this one. Source is defined up top
    source.data = array

    # Fourth, bin the values into lat, long points for the dataframe
    dfs = xr.DataArray(source, name = "data")
    pdf = dfs.to_dataframe()
    step = .25
    to_bin = lambda x: np.floor(x / step) * step
    pdf["latbin"] = pdf.index.get_level_values('y').map(to_bin)
    pdf["lonbin"] = pdf.index.get_level_values('x').map(to_bin)
    pdf['gridx']= pdf['lonbin'].map(londict)
    pdf['gridy']= pdf['latbin'].map(latdict)
    grid2 = np.copy(grid)
    grid2[np.isnan(grid2)] = 0
    pdf['grid'] = grid2[pdf['gridy'],pdf['gridx']]
    pdf['grid'] = pdf['grid'].apply(int).apply(str)
    pdf['data'] = pdf['data'].astype(float).round(3)
    pdf['printdata'] = "GRID #: " + pdf['grid'] +"<br>Data: " + pdf['data'].apply(str)
    groups = pdf.groupby(("latbin", "lonbin"))
    df_flat = pdf.drop_duplicates(subset=['latbin', 'lonbin'])
    df= df_flat[np.isfinite(df_flat['data'])]

    # Add Grid IDs
    colorscale = [[0, 'rgb(2, 0, 68)'], [0.35, 'rgb(17, 123, 215)'],# Make darker (pretty sure this one)
                    [0.45, 'rgb(37, 180, 167)'], [0.55, 'rgb(134, 191, 118)'],
                    [0.7, 'rgb(249, 210, 41)'], [1.0, 'rgb(255, 249, 0)']] # Make darker

# Create the scattermapbox object
    data = [
        dict(
        type = 'scattermapbox',
#        locationmode = 'USA-states',
        lon = df['lonbin'],
        lat = df['latbin'],
        text = df['printdata'],
        mode = 'markers',
        marker = dict(
            colorscale = colorscale,
            cmin = 0,
            color = df['data'],
            cmax = df['data'].max(),
            opacity=0.85,
            colorbar=dict(
                title= "Frequency<br>(out of 199)",
                textposition = "auto",
                orientation = "h"
                )
            )
        )]

    layout['title'] = "USDM | " + DMlabels.get(usdm_level) +"+ Drought Frequency"
    layout['mapbox']['zoom'] = 2

    # Seventh wrap the data and layout into one
    figure = dict(data=data, layout=layout)
#    return {'figure':figure,'info': index_package_all}
    return figure



# In[]:
@app.callback(Output('hit_graph', 'figure'),
              [Input('signal','children')])
def riskcountGraph(signal):
    # Get data
    df = retrieve_data(signal)

    # Transform the argument list back to normal
    signal = json.loads(signal)

    # Unpack signals
    index_choice = signal[0]
    usdm_level = signal[1]
    strike_level = signal[2]


    # Get desired array
    [basisrisk, droughtchances, hits, rainchance] = df

    # Second, convert data back into an array, but in a from xarray recognizes
    array = np.array([hits],dtype = "float32")

    # Third, change the source array to this one. Source is defined up top
    source.data = array

    # Fourth, bin the values into lat, long points for the dataframe
    dfs = xr.DataArray(source, name = "data")
    pdf = dfs.to_dataframe()
    step = .25
    to_bin = lambda x: np.floor(x / step) * step
    pdf["latbin"] = pdf.index.get_level_values('y').map(to_bin)
    pdf["lonbin"] = pdf.index.get_level_values('x').map(to_bin)
    pdf['gridx']= pdf['lonbin'].map(londict)
    pdf['gridy']= pdf['latbin'].map(latdict)
    grid2 = np.copy(grid)
    grid2[np.isnan(grid2)] = 0
    pdf['grid'] = grid2[pdf['gridy'],pdf['gridx']]
    pdf['grid'] = pdf['grid'].apply(int).apply(str)
    pdf['data'] = pdf['data'].astype(float).round(3)
    pdf['printdata'] = "GRID #: " + pdf['grid'] +"<br>Data: " + pdf['data'].apply(str)
    groups = pdf.groupby(("latbin", "lonbin"))
    df_flat = pdf.drop_duplicates(subset=['latbin', 'lonbin'])
    df= df_flat[np.isfinite(df_flat['data'])]
    # Add Grid IDs
    colorscale = [[0, 'rgb(2, 0, 68)'], [0.35, 'rgb(17, 123, 215)'],# Make darker (pretty sure this one)
                    [0.45, 'rgb(37, 180, 167)'], [0.55, 'rgb(134, 191, 118)'],
                    [0.7, 'rgb(249, 210, 41)'], [1.0, 'rgb(255, 249, 0)']] # Make darker

# Create the scattermapbox object
    data = [
        dict(
        type = 'scattermapbox',
#        locationmode = 'USA-states',
        lon = df['lonbin'],
        lat = df['latbin'],
        text = df['printdata'],
        mode = 'markers',
        marker = dict(
            colorscale = colorscale,
            cmin = 0,
            color = df['data'],
            cmax = df['data'].max(),
            opacity=0.85,
            colorbar=dict(
                title= "Frequency<br>(out of 199)",
                textposition = "auto",
                orientation = "h"
                )
            )
        )]

    layout['title'] = ("Non-Payment Count<br>" + str(int(strike_level*100)) + "% Rain Index  &  " + DMlabels.get(usdm_level) + "+ USDM")

    layout['mapbox']['zoom'] = 2
    # Seventh wrap the data and layout into one
    figure = dict(data=data, layout=layout)
#    return {'figure':figure,'info': index_package_all}
    return figure

# In[]:
@app.callback(Output('basis_graph', 'figure'),
              [Input('signal','children')])
def basisGraph(signal):
    # Get data
    df = retrieve_data(signal)
    [basisrisk, droughtchances, hits, rainchance] = df

    # Transform the argument list back to normal
#    if not signal:
#        signal= source_signal
    signal = json.loads(signal)

    # Unpack signals
    index_choice = signal[0]
    usdm_level = signal[1]
    strike_level = signal[2]
    statefilter = signal[3]
    typeof = str(type(statefilter))

    # Second, convert data back into an array, but in a form xarray recognizes
    array = np.array([basisrisk],dtype = "float32")

    # Third, change the source array to this one. Source is defined up top
    source.data = array

    # Fourth, bin the values into lat, long points for the dataframe
    dfs = xr.DataArray(source, name = "data")
    pdf = dfs.to_dataframe()
    step = .25
    to_bin = lambda x: np.floor(x / step) * step
    pdf["latbin"] = pdf.index.get_level_values('y').map(to_bin)
    pdf["lonbin"] = pdf.index.get_level_values('x').map(to_bin)
    pdf['gridx']= pdf['lonbin'].map(londict)
    pdf['gridy']= pdf['latbin'].map(latdict)
    grid2 = np.copy(grid)
    grid2[np.isnan(grid2)] = 0
    pdf['grid'] = grid2[pdf['gridy'],pdf['gridx']]
    pdf['grid'] = pdf['grid'].apply(int).apply(str)
    pdf['data'] = pdf['data'].astype(float).round(3)
    pdf['printdata'] = "GRID #: " + pdf['grid'] +"<br>Data: " + pdf['data'].apply(str)
    groups = pdf.groupby(("latbin", "lonbin"))
    df_flat = pdf.drop_duplicates(subset=['latbin', 'lonbin'])
    df= df_flat[np.isfinite(df_flat['data'])]

    # Add Grid IDs
    colorscale = [[0, 'rgb(2, 0, 68)'], [0.35, 'rgb(17, 123, 215)'],# Make darker (pretty sure this one)
                    [0.45, 'rgb(37, 180, 167)'], [0.55, 'rgb(134, 191, 118)'],
                    [0.7, 'rgb(249, 210, 41)'], [1.0, 'rgb(255, 249, 0)']] # Make darker

# Create the scattermapbox object
    data = [
        dict(
        type = 'scattermapbox',
#        locationmode = 'USA-states',
        lon = df['lonbin'],
        lat = df['latbin'],
        text = df['printdata'],
        mode = 'markers',
        marker = dict(
            colorscale = colorscale,
            cmin = 0,
            color = df['data'],
            cmax = df['data'].max(),
            opacity=0.85,
            colorbar=dict(
                title= "Risk Ratio",
                textposition = "auto",
                orientation = "h"
                )
            )
        )]

    # Return order to help with average value:
    # Weight by the number of drought events
    average = str(round(np.nansum(droughtchances*basisrisk)/np.nansum(droughtchances),4))
#    average = np.nanmean(basisrisk)
    layout['title'] = ("Non-Payment Likelihood <br>" + str(int(strike_level*100)) + "% Rain Index  &  " 
                    + DMlabels.get(usdm_level) + "+ USDM  |  Average: " + average)


#    layout['title'] = typeof
#     Seventh wrap the data and layout into one
    figure = dict(data=data, layout=layout)
#    return {'figure':figure,'info': index_package_all}
    return figure


# In[]:
# Main
if __name__ == '__main__':
    app.run_server()#,debug  =True



