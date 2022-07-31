import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy
import tkinter
from tkinter import filedialog
tkinter.Tk().withdraw()

# Functions without importing package
P_atm = 0.0
R = 287.15

# Calibration Data
CaliData = {'Channel':[], 'Slope':[], 'Intercept':[]}
CaliData['Channel'] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
CaliData['Slope'] = [0.0381040757689512, 0.0380786462847762, 0.0380970846012763, 0.0381066600054133, 0.0380630019995389, 0.0380026646965952, 0.0380227461155428, 0.0380279762258936, 0.0381013507548507, 0.0381320275223357, 0.0381385115128278, 0.0380980314084898, 0.0380735204806152, 0.0381392187594341, 0.0379738927682319, 0.0379216984683499, 0.0379903348630159, 0.0381246241124626, 0.0382393984685897, 0.0380880954681932, 0.038079728871159, 0.0381101196947877, 0.0381565797722527, 0.0380953384868586, 0.0381261542908074, 0.0382179055644527, 0.0381791597492622, 0.0380855491984027, 0.0381462386897156, 0.0381804208458629, 0.0380447183724224, 0.0391563971381895]
CaliData['Intercept'] = [0.4914571389281081, 0.5028715554846253, 0.4995455331509792, 0.4987194933735539, 0.4964456739071727, 0.4983660999575456, 0.49723503982062, 0.4967467539157622, 0.4940347477115252, 0.4958196202561211, 0.4898696692891393, 0.4961451868894273, 0.4990685077875754, 0.4935547958307902, 0.4919306889918573, 0.5178367381359652, 0.5039024759189048, 0.4892013508522126, 0.4895313666327152, 0.4943229378482434, 0.4966447256480775, 0.4875509175535839, 0.4952119356005924, 0.4940119977074184, 0.4969002312527286, 0.4863697000251403, 0.4933758049375765, 0.4964665046105097, 0.4939810462464806, 0.4882600515449251, 0.5022520323991846, -0.0346328464744767]

CaliData = pd.DataFrame(CaliData)


def mm_read_lvm(filename, columns=numpy.arange(3,32)):
    Col_to_read = ['X_Value', 'Pstat', 'P1', 'DP', 'Untitled']
    for i in columns:
        Col_to_read.append('Voltage_'+str(i-3))
    print('Reading Columns: '+str(Col_to_read))

    Data = lvm_read_lvm(filename, Col_to_read)

    Data.rename(columns={'Pstat': 'Pitot_Static',
                         'P1': 'Section_Static',
                         'DP': 'Pitot_Delta',
                         'Untitled': 'Temp'},
                         inplace=True)
    # for i in range(len(Data)):
    #     Data['Temp'].iloc[i] = Data.iloc[(i//1000)*1000]['Temp']
    Data['Temp'] = Data['Temp'].fillna(method='ffill')
    Data['Density'] = P_atm/(R*(Data['Temp']+273.15))
    Data['a'] = numpy.sqrt(1.4*R*(Data['Temp']+273.15))

    # Set Pitot and Section Pressures
    Data['Pitot_P'] = (Data['Pitot_Static']-CaliData.iloc[0]['Intercept'])/CaliData.iloc[0]['Slope']
    Data['Pitot_Delta_P'] = ((Data['Pitot_Delta']-CaliData.iloc[31]['Intercept'])/CaliData.iloc[31]['Slope'])
    Data['Section_P'] = (Data['Section_Static']-CaliData.iloc[1]['Intercept'])/CaliData.iloc[1]['Slope']
    Data['Mach'] = numpy.sqrt(((((Data['Pitot_Delta_P']+Data['Pitot_P'])/Data['Section_P'])**(0.4/1.4))-1)*(2/0.4))

    # Voltage Calibration
    for k in columns:
        Data['P'+str(k)] = (Data['Voltage_'+str(k-3)]-CaliData.iloc[k-2]['Intercept'])/CaliData.iloc[k-2]['Slope']
        Data['CP'+str(k)] = (Data['P'+str(k)]-P_atm/1000)/(0.7*P_atm/1000*Data['Mach']**2)
    return Data

def lvm_read_lvm(filename, cols):
    EoH = '***End_of_Header***'
    file = open(filename, 'r')
    Lines = file.readlines()
    count = 0
    count_eoh = 0
    for line in Lines:
        if (line.strip() == EoH) and (count_eoh<1):
            count_eoh+=1
        elif line.strip() == EoH:
            break
        count+=1
    file.close()
    Data = pd.read_csv(filename, skiprows=count+1, sep='\t', usecols=cols)
    return Data



filepath = filedialog.askopenfilename()
correct = False
while correct == False:
    plot_all = input('Plot all inputs? (y/n): ')
    if  plot_all == 'n':
        columns = input('Pressure inputs to plot: ').split(',')
        columns = list(map(int, columns))
        correct = True
    elif plot_all == 'y':
        import numpy
        columns = numpy.arange(3, 32)
        correct = True


Data = mm_read_lvm(filepath, columns=columns)

figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.02, row_heights=[0.75,0.25])

static = input('Plot tunnel static? y/n: ')
if static == 'y':
    figure.add_trace(
        go.Scatter(
            x=Data['X_Value'],
            y=Data['Section_P'],
            name='Tunnel Static',
            hovertemplate='P: %{y:.2f} kPa <br> Time: %{x:.2f}s'
        ),
        row=1, col=1
    )

for i in columns:
    figure.add_trace(
        go.Scatter(
            x=Data['X_Value'],
            y=Data['P'+str(i)],
            name='P'+str(i),
            hovertemplate='P: %{y:.2f} kPa <br> Time: %{x:.2f}s'
        ),
        row=1, col=1
    )

figure.add_trace(
    go.Scatter(
        x=Data['X_Value'],
        y=Data['Mach'],
        name='Mach',
        showlegend=False,
            hovertemplate='Mach %{y:.2f} <br> Time: %{x:.2f}s'
    ),
    row=2, col=1
)

figure.update_yaxes(title_text='Static Pressure [kPa]', row=1, col=1)
figure.update_yaxes(title_text='Mach', row=2, col=1)
figure.update_xaxes(title_text='Time [s]', row=2, col=1)

figure.show()
