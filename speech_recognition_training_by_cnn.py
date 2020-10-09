#!/usr/bin/env python
# coding: utf-8



# 讀取 整理過 的資料庫
# gscV2_data.npz == 2.96 GB (3,179,793,526 位元組)
# 它來自  data_speech_commands_v0.02.tar.gz == 2.26 GB (2,428,923,189 位元組)
# 或      train.tar.gz == 2.26 GB (2,428,923,189 位元組)
# 但不包含 test.tar.gz ==  107 MB (   112,563,277 位元組)
#
# 此檔案(gscV2_data.npz) 適合 numpy 讀取，讀取速度相當快。
# 它已經根據資料庫原作者建議，
# 分成 train(84,843), val (9,981), test(11,005) 3個子集合。
# 又從 _background_noise_ 中取出 402 段 1sec 語音，併入 train 中
# 因此，讀出的 3個子集合，內含音檔數 分別為... 
# train(85,245), val (9,981), test(11,005)
#
# 原資料庫宣稱所有語音當都是 1sec, fs= 16000Hz，
# 但事實上有些檔案不及 1sec, 有些又超過 1sec，
# 在 gscV2_data.npz 中， 我們有注意到這個問題，並加以解決，
# 對於太短的檔案僅是簡單的補0來增長，又把過長檔案的兩端各剪掉一點。
# 確定 所有檔案的長度確實為 1sec = 16000點 的語音資料。
#
# 所有的語音資料的值(x_value)已經轉換成 -1.0 ~ +1.0 的 'float32' 實數
# 而其 標籤值(y_value) 為 0 ~ 35 的  'int32' 整數值
#     0 代表 _silence_ 或 _background_noise_
#     1~35 代表 資料庫之詞彙種類
#
#
# 請來這裡撈這個整理過的檔案：
# https://1drv.ms/u/s!AjlltK85sd7q2K1ICtdHw29F_wf3cA?e=wGdOpO
# 然後放在 本程式可以讀得到的地方，
# 若與本程式同一資料夾，
# 則上述 basePath 設定如下: 
#
# basePath= './'     # 代表「目前」的資料夾
from  sys import argv
import numpy as np
import time
import tensorflow as tf
from tensorflow.keras.layers import Input, Conv2D, Flatten, Dense, Dropout
from tensorflow.keras.layers import MaxPooling2D, AveragePooling2D
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.models    import Model, load_model
import matplotlib.pyplot as pl
import sounddevice as sd
from matplotlib import pyplot as pl

# training檔案放置位置
f = argv[1]
npzFile = np.load(f)

'''
basePath = '../ryDatasets/gscV2/'
file     = 'gscV2_data.npz'

npzFile = np.load(basePath+file)
'''

# 將檔案解壓縮


x_train = npzFile['x_trainWithSil']    
y_train = npzFile['y_trainWithSil']    
x_val   = npzFile['x_val']      
y_val   = npzFile['y_val']
x_test  = npzFile['x_test']     
y_test  = npzFile['y_test']     


# 儲存原本的資料

x_train_all = x_train
y_train_all = y_train

x_val_all   = x_val
y_val_all   = y_val

x_test_all  = x_test
y_test_all  = y_test


# In[4]:


# 完整的詞彙列表35 個英文詞 + 'silence' = 36 個
# 建議使用import
f = argv[2]

lines = f.readlines()
ryGscList = [line.rstrip('\n') for line in lines]



'''
ryGscList=[ 
 '_silence_',
 
 'one',  'two', 'three', 'four', 'five',
 'six', 'seven', 'eight', 'nine', 'zero',
 
 'yes', 'no',
 'go', 'stop',
 'on', 'off',
 'up', 'down',
 'left', 'right',
 'forward', 'backward',
 
 'marvin', 'sheila',
 'dog', 'cat',
 'bird', 'bed',
 'happy', 'house',
 'learn', 'follow',
 'tree', 'visual',
 'wow',
 
 '_unknown_'
 ]
'''

# In[5]:


# 統計資料庫資料

distTrain = [y_train[y_train==x].size for x in range(len(ryGscList))]
distTest  = [y_test[y_test==x].size   for x in range(len(ryGscList))]
distVal   = [y_val[y_val==x].size     for x in range(len(ryGscList))]

distTrain = np.array(distTrain)
distTest  = np.array(distTest)
distVal   = np.array(distVal)

distAll= distTrain + distTest + distVal

aL= list(zip(list(range(len(ryGscList))), 
             ryGscList,  
             list(distAll)))

bL= sorted(aL, key= lambda x:x[1])

cL= sorted(aL, key= lambda x:-x[2])


# In[6]:
# 編號 單字 資料筆數

aL
_='''
aL
Out[49]: 
[(0, '_silence_', 402),
 (1, 'one', 3890),
 (2, 'two', 3880),
 (3, 'three', 3727),
 (4, 'four', 3728),
 (5, 'five', 4052),
 (6, 'six', 3860),
 (7, 'seven', 3998),
 (8, 'eight', 3787),
 (9, 'nine', 3934),
 (10, 'zero', 4052),
 (11, 'yes', 4044),
 (12, 'no', 3941),
 (13, 'go', 3880),
 (14, 'stop', 3872),
 (15, 'on', 3845),
 (16, 'off', 3745),
 (17, 'up', 3723),
 (18, 'down', 3917),
 (19, 'left', 3801),
 (20, 'right', 3778),
 (21, 'forward', 1557),
 (22, 'backward', 1664),
 
 (23, 'marvin', 2100),
 (24, 'sheila', 2022),
 (25, 'dog', 2128),
 (26, 'cat', 2031),
 (27, 'bird', 2064),
 (28, 'bed', 2014),
 (29, 'happy', 2054),
 (30, 'house', 2113),
 (31, 'learn', 1575),
 (32, 'follow', 1579),
 (33, 'tree', 1759),
 (34, 'visual', 1592),
 (35, 'wow', 2123),
 
 (36, '_unknown_', 0)]

'''


# In[7]:


# 設定 3個子集合(Dgt, Yes, Oth)，以及全部(All)。

#  Dgt= 10 個數字
DgtList =  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Yes= 12 個 Cmd，    「是、否、去、停、 開、關、上、下、  左、右、前、後」。
YesList =  [0, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

# 其他 13 個。 + 1 個 0:"_silence_", 1 個 36:"_unknown_" 
OthList = [0, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]

# 總共 10 + 12 + 13 == 35 +1 (_silence_) +1 (_unknown_)
AllList = list(range(len(ryGscList)))


# In[8]:


# 選好 CmdList 即可完整跑到底....
# Dgt 辨識率最高，可先選來做做看

# 設定要training的範圍
  
CmdSet  = set(DgtList).union(set(YesList))
UnkSet  = set(AllList)-CmdSet

CmdList = np.array(sorted(CmdSet))
UnkList = np.array(sorted(UnkSet))



# 選擇 語音資料子集合來建立 模型

# rename "marvin" as "_unknown_"

y_train[np.isin(y_train_all, UnkList)]= 23 
y_val[  np.isin(y_val_all,   UnkList)]= 23 
y_test[ np.isin(y_test_all,  UnkList)]= 23 

ryGscList[23]= '_unknown_'  


# In[10]:


# 檢查一下 類別總數 (nCaters)，
# Dgt= 11, Yes=11, Oth=16, All=36
#

nCategs= len(set(y_train)) #36 #c_train.size #36

print(f'nCategs= {nCategs}')

#以上為檔案處理



## mfcc

def ryFeature(x, 
           sample_rate= 16000, 
           
           frame_length=  512, #1024,
           frame_step=    160, #128,  # frame_length//2
           
           num_mel_bins=     512//8, #32, #100,   #128,
           lower_edge_hertz=   0,     # 0
           upper_edge_hertz= 16000/2, # sample_rate/2   
           
           mfcc_dim= 16 #13
           ):
    # 傅立葉轉換
    stfts= tf.signal.stft(x, 
                          frame_length, #=  256, #1024, 
                          frame_step, #=    128,
                          #fft_length= 1024
                          pad_end=True
                          )
    # 取絕對值
    spectrograms=     tf.abs(stfts)
    # 取自然對數
    log_spectrograms= tf.math.log(spectrograms)# + 1e-10)
    
    # Warp the linear scale spectrograms into the mel-scale.
    num_spectrogram_bins= stfts.shape[-1]  #.value
    
    
    linear_to_mel_weight_matrix= tf.signal.linear_to_mel_weight_matrix(
          num_mel_bins, 
          num_spectrogram_bins, 
          sample_rate, 
          lower_edge_hertz,
          upper_edge_hertz)
    
    
    W= linear_to_mel_weight_matrix
      
    W1= W/ tf.math.reduce_sum(W, axis=0)  # 我把 那些 三角形濾波器 sum to one 了。
    
    mel_spectrograms= spectrograms @ W1  # 這行取代 tensordot()
   
    
    # Compute a stabilized log to get log-magnitude mel-scale spectrograms.
    log_mel_spectrograms= tf.math.log(mel_spectrograms + 1e-10) # 加上 1e-10 避免 log(0) 的出現
    
    # Compute MFCCs from log_mel_spectrograms and take the first 13.
    mfccs= tf.signal.mfccs_from_log_mel_spectrograms(
          log_mel_spectrograms)[..., :mfcc_dim]
    
    feature= {'mfcc':               mfccs, 
              'log_mel_spectrogram':log_mel_spectrograms, 
              
              'log_spectrogram':    log_spectrograms,  # 以下 2個 不太有用，留下僅供參考。
              'spectrogram':        spectrograms}
    
    return  feature

def get_all_fearure(all_x, batch_size= 1000):
    t0= time.time()
    
    x= all_x.astype(np.float32)
    
    
    i=0
    XL=[]
    while i < x.shape[0]:
        
        if i+batch_size<=x.shape[0]:
            xx= x[i:i+batch_size]
        else:
            xx= x[i:]
        
        X= ryFeature(xx)['mfcc']
        
        
        i  += batch_size
        XL += [X]
    
    # 讓結果平坦化之後接到最基本的神經網絡
    XL= tf.concat(XL, axis= 0)
    print('XL.shape={}'.format(XL.shape))
    
    dt= time.time()-t0
    print('tf.signal.stft, 執行時間 dt= {}'.format(dt))

    return XL

print('.... get_all_fearure() .... ')



t0= time.time()

X_test=     get_all_fearure(x_test)
X_val=      get_all_fearure(x_val)
X_train=    get_all_fearure(x_train)

dt= time.time()- t0
print('... get_all_fearure() ... dt(sec)= {:.3f}'.format(dt))


# In[13]:


# 檢查 X_train 的 形狀
nTime, nFreq= X_train[0].shape



# In[14]:


# 對 X_* 作 正規化

def normalize(x, axis= None):   
    if axis== None:
        x= (x - tf.math.reduce_mean(x)
            )/tf.math.reduce_std(x)
    else:
        x= (x - tf.math.reduce_mean(x, axis)
            )/tf.math.reduce_std(x, axis)
    
    return x

print('.... normalize() ....')

X_train= tf.reshape(X_train, (-1, nTime, nFreq ,1))
X_val=   tf.reshape(X_val,   (-1, nTime, nFreq ,1))
X_test=  tf.reshape(X_test,  (-1, nTime, nFreq ,1))

X_train=     normalize(X_train) 
X_val=       normalize(X_val)   
X_test=      normalize(X_test)  




# In[16]:


# 以上先把語音資料庫處理完畢，並作了 特徵擷取 (mfcc)
# 接著要進入 cnn + dnn 神經網路 建模了....


# 啟動 tf.keras
tf.keras.backend.clear_session()  

# 準備好模型的檔名以便訓練時儲存。
fnModel= 'ryAsr2020_ryTrainModel.hdf5'
print(f"... fnModel= {fnModel}")


# In[19]:
#
#  開始設立 CNN 模型
def ryCnn(nTime, nFreq, nCategories):
    
    x= Input(shape= (nTime, nFreq, 1))
    
    h= x      
    h= Conv2D(10,   (10, nFreq), 
              activation='relu', 
              padding='same', 
              strides=(2, nFreq)
              )(h)    
    h= MaxPooling2D((2,1), padding='same')(h)    
    h= Dropout(0.1)(h)
           
    h= Flatten()(h)
    h= Dense(100,  activation='relu')(h)  
    h= Dropout(0.1)(h)      
    h= Dense(nCategs,  activation='softmax')(h)    
    y= h
    
    m= Model(inputs=  x, 
             outputs= y)    
    m.summary()
    return m


# In[20]:


m= ryCnn(nTime, nFreq,  nCategories= nCategs) 
    
m.compile(  
        loss=    'sparse_categorical_crossentropy',
        metrics= ['accuracy'])

es= EarlyStopping(
        monitor=   'val_loss', 
        min_delta= 1e-10,
        patience=  10, 
        mode=      'min', 
        verbose=   1) 

mc= ModelCheckpoint(fnModel, 
        monitor=    'val_accuracy', 
        verbose=    1, 
        save_best_only= True, 
        mode=      'max')
  

# In[21]:


### 正式跑【模型訓練】

t0= time.time() 

h= m.fit(X_train, y_train,
         
        batch_size=100, #1000, # 1000
        epochs=    100,
        
        callbacks=[es, mc],
        
        #validation_split= 0.1
        validation_data= (X_val, y_val)
        )

dt= time.time()- t0
print('... h= m.fit() ... dt(sec)= {}'.format(dt))

# In[22]:

# 計算測試辨識率
m.evaluate(X_test,      y_test,      verbose=2)


# In[23]:

#  找 1 個 語音來測試
randomIndex= 1000

x= x_test[randomIndex]
X= X_test[randomIndex]

X=    tf.reshape(X, (1, X.shape[0], X.shape[1], 1))
prob= m.predict(X)[0]

sortIndex=  prob.argsort()[-1::-1]
sortProb=   prob[sortIndex]

sortPred=    np.array(ryGscList)[sortIndex] ## 這行有點錯綜複雜！！

print(f'sortPred= {sortPred}') # topN recognition result
print(f'sortProb= {sortProb}')


# In[24]:


# 資料結果視覺化

sd.play(x, 16000)

pl.subplot(2,1,1);pl.grid('on');pl.plot(x)

X= X.numpy().squeeze().transpose()
pl.subplot(2,1,2);pl.grid('on');pl.contourf(X)#, levels=100)


# In[25]:


# 繪製訓練過程 acc 變化圖



def plot_train_history(h):
    v0= h.history['accuracy']
    v1= h.history['val_accuracy']
    pl.plot(v0, label='accuracy')
    pl.plot(v1, label='val_accuracy')
    pl.legend()
    pl.grid('on')
    pl.show()

plot_train_history(h)


# In[26]:


# 結果測試

labels= np.array(ryGscList)

fnModel= 'ryAsr2020_ryTrainModel.hdf5'

model= load_model(fnModel)


def predict(x, probOut= False, indexMapping= None):
    
    x= tf.reshape(x, (1, x.shape[0], x.shape[1], 1))
    
    prob=  model.predict(x)
    index= np.argmax(prob[0])
    maxProb= np.max(prob[0])
    
    if indexMapping != None:
        index= indexMapping[index]
        
    y= labels[index]
    
    if probOut==True:
        return (y, maxProb)
    else:
        return y


def recWav(x, probOut= False): #, indexMapping= None):
    
    x= x.flatten()    

    X= ryFeature(x)['mfcc']
        
    X= normalize(X)  # normalized for only one utterence x

    #y= predict(X, probOut= probOut, indexMapping= indexMapping)
    
    X= tf.reshape(X, (1, X.shape[0], X.shape[1], 1))
    
    prob=  model.predict(X)[0]
    index=   prob.argsort()[-1::-1]#np.argmax(prob)
    maxProb= prob[index] #np.max(prob)
    
    #if indexMapping != None:
    #    index= indexMapping[index]
    #####index= CmdList[index]    
    
    y= labels[index]
    
    if probOut==True:
        y= np.vstack((y, maxProb))
    return y
    



# In[27]:


T=  1     # Duration of recording
fs= 16000  # Sample rate

def speak_and_recognize():

    x= sd.rec(int(T*fs), 
            samplerate= fs, 
            channels= 1, 
            dtype='float32')

    sd.wait()  # Wait until recording is finished

    y= recWav(x, probOut=True)#, indexMapping= CmdList) 

    print('y= {}'.format(y))

print(f'''
press 'q' to quit 
or another key to record 1 sec of speech ...
you can say anyword in the list: 
{labels[CmdList]}
''')

for i in range(100):

    aKey= input() 
    if aKey=='q': break

    speak_and_recognize()


# In[28]:



