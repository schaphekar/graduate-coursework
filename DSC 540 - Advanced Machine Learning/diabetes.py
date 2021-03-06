### Import necessary modules
import sys
import csv
import math
import numpy as np
from operator import itemgetter
import time

### Import ML libraries
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingClassifier, AdaBoostClassifier, RandomForestClassifier
from sklearn.neural_network import MLPClassifier

from sklearn.externals import joblib
from sklearn.feature_selection import RFE, VarianceThreshold, SelectFromModel
from sklearn.feature_selection import SelectKBest, mutual_info_regression, mutual_info_classif, chi2

from sklearn import metrics
from sklearn.model_selection import cross_validate, train_test_split
from sklearn.preprocessing import KBinsDiscretizer, scale

### Handle warnings
import warnings, sklearn.exceptions
warnings.filterwarnings("ignore", category=sklearn.exceptions.ConvergenceWarning)

### Global parameters
target_idx = 0                   # Index of Target variable
cross_val = 0                    # Control Switch for CV
norm_target = 0                  # Normalize target switch
norm_features = 0                # Normalize target switch
binning = 0                      # Control Switch for Bin Target
bin_cnt = 2                      # If bin target, this sets number of classes
feat_select = 0                  # Control Switch for Feature Selection
fs_type = 2                      # Feature Selection type (1=Stepwise Backwards Removal, 2=Wrapper Select, 3=Univariate Selection)
lv_filter = 0                    # Control switch for low variance filter on features
feat_start = 1                   # Start column of features

### Set global model parameters
rand_st=1                        # Set Random State variable for randomizing splits on runs

### Load Data
file1 = csv.reader(open('pimadiabetes.csv'), delimiter=',', quotechar='"')

# Read Header Line
header = next(file1)            

# Read data
data=[]
target=[]

for row in file1:
    
    if row[target_idx]=='':                    # If target is blank, skip row                       
        continue
    else:
        target.append(float(row[target_idx]))  # If pre-binned class, change float to int

    # Load row into temp array, cast columns  
    temp=[]
                 
    for j in range(feat_start,len(header)):
        if row[j]=='':
            temp.append(float())
        else:
            temp.append(float(row[j]))

    # Load temp into Data array
    data.append(temp)
  
# Test Print
print(header)
print(len(target),len(data))
print('\n')

data_np=np.asarray(data)
target_np=np.asarray(target)

### Feature Selection

### Low Variance Filter
if lv_filter==1:
    print('--LOW VARIANCE FILTER ON--', '\n')
    
    # LV Threshold
    sel = VarianceThreshold(threshold=0.5)                                          # Removes any feature with less than 20% variance
    fit_mod=sel.fit(data_np)
    fitted=sel.transform(data_np)
    sel_idx=fit_mod.get_support()

    # Get lists of selected and non-selected features (names and indexes)
    temp=[]
    temp_idx=[]
    temp_del=[]
    for i in range(len(data_np[0])):
        if sel_idx[i]==1:                                                           # Selected Features get added to temp header
            temp.append(header[i+feat_start])
            temp_idx.append(i)
        else:                                                                       # Indexes of non-selected features get added to delete array
            temp_del.append(i)

    print('Selected:', temp)
    print('Features (total, selected):', len(data_np[0]), len(temp))
    print('\n')

    # Filter selected columns from original dataset
    header = header[0:feat_start]
    for field in temp:
        header.append(field)
    data_np = np.delete(data_np, temp_del, axis=1) 

if feat_select==1:
    '''Three steps:
       1) Run Feature Selection
       2) Get lists of selected and non-selected features
       3) Filter columns from original dataset
       '''
    
    print('--FEATURE SELECTION ON--', '\n')
    
    ## 1) Run Feature Selection
    # Wrapper Select via model
    if fs_type==2:
        rgr = DecisionTreeRegressor(criterion='friedman_mse', splitter='best', max_depth=None, min_samples_split=3, min_samples_leaf=1, max_features=None, random_state=rand_st)
        sel = SelectFromModel(rgr, prefit=False, threshold='mean', max_features=None)                   
        print ('Wrapper Select: ')

        fit_mod=sel.fit(data_np, target_np)    
        sel_idx=fit_mod.get_support()


    ## 2) Get lists of selected and non-selected features (names and indexes)
    temp=[]
    temp_idx=[]
    temp_del=[]
    for i in range(len(data_np[0])):
        if sel_idx[i]==1:                                                # Selected Features get added to temp header
            temp.append(header[i+feat_start])
            temp_idx.append(i)
        else:                                                            # Indexes of non-selected features get added to delete array
            temp_del.append(i)
    print('Selected:', temp)
    print('Features (total/selected):', len(data_np[0]), len(temp))
    print('\n')
            
               
    ## 3) Filter selected columns from original dataset
    header = header[0:feat_start]
    for field in temp:
        header.append(field)
    data_np = np.delete(data_np, temp_del, axis=1) 
    

### Train SciKit Models
print('--ML Model Output--', '\n')

### Test/Train split
data_train, data_test, target_train, target_test = train_test_split(data_np, target_np, test_size=0.35)

### Regressors
if binning==0 and cross_val==0:
    
    # SciKit Decision Tree Regressor
    rgr = DecisionTreeRegressor(criterion='friedman_mse', splitter='best', max_depth=None, min_samples_split=3, min_samples_leaf=1, max_features=None, random_state=rand_st)
    rgr.fit(data_train, target_train)

    scores_RMSE = math.sqrt(metrics.mean_squared_error(target_test, rgr.predict(data_test)))
    print('Decision Tree RMSE:', scores_RMSE)
    scores_Expl_Var = metrics.explained_variance_score(target_test, rgr.predict(data_test))
    print('Decision Tree Expl Var:', scores_Expl_Var)

### Cross-Val Regressors
if binning==0 and cross_val==1:
    
    # Setup Crossval regression scorers
    scorers = {'Neg_MSE': 'neg_mean_squared_error', 'expl_var': 'explained_variance'} 
    
    # SciKit Decision Tree Regressor - Cross Val
    start_ts=time.time()
    rgr = DecisionTreeRegressor(criterion='mse', splitter='best', max_depth=None, min_samples_split=3, min_samples_leaf=1, max_features=None, random_state=rand_st)
    scores = cross_validate(rgr, data_np, target_np, scoring=scorers, cv=5)

    scores_RMSE = np.asarray([math.sqrt(-x) for x in scores['test_Neg_MSE']])                # Turns negative MSE scores into RMSE
    scores_Expl_Var = scores['test_expl_var']
    print("Decision Tree RMSE:: %0.2f (+/- %0.2f)" % ((scores_RMSE.mean()), (scores_RMSE.std() * 2)))
    print("Decision Tree Expl Var: %0.2f (+/- %0.2f)" % ((scores_Expl_Var.mean()), (scores_Expl_Var.std() * 2)))
    print("CV Runtime:", time.time()-start_ts)

### Classifiers
if cross_val==0:   
    
    # SciKit Random Forest
    clf = RandomForestClassifier(n_estimators=100, max_depth=None, min_samples_split = 3, criterion = 'entropy', random_state = rand_st)  
    clf.fit(data_train, target_train)

    scores_ACC = clf.score(data_test, target_test)                                                                                                                          
    print('Random Forest Acc:', scores_ACC)
    scores_AUC = metrics.roc_auc_score(target_test, clf.predict_proba(data_test)[:,1])                                                                                      
    print('Random Forest AUC:', scores_AUC)                                                       # AUC only works with binary classes, not multiclass            
 
### Cross-Val Classifiers
if cross_val==1:
    
    #Setup Crossval classifier scorers
    scorers = {'Accuracy': 'accuracy', 'roc_auc': 'roc_auc'}                                                                                                                
    
    # SciKit Random Forest - Cross Val
    start_ts=time.time()
    clf = RandomForestClassifier(n_estimators=100, max_depth=None, min_samples_split = 3, criterion = 'entropy', random_state = rand_st)  
    scores = cross_validate(clf,data_np,target_np,scoring=scorers,cv=5)                                                                                        

    scores_Acc = scores['test_Accuracy']                                                                                                                                    
    print("Random Forest Acc: %0.2f (+/- %0.2f)" % (scores_Acc.mean(), scores_Acc.std() * 2))                                                                                                    
    scores_AUC= scores['test_roc_auc']                                                                     # Only works with binary classes, not multiclass                  
    print("Random Forest AUC: %0.2f (+/- %0.2f)" % (scores_AUC.mean(), scores_AUC.std() * 2))                           
    print("CV Runtime:", time.time()-start_ts)
    
### Cross-Val Classifiers
if binning==1 and cross_val==1:
    
    # Setup Crossval classifier scorers
    scorers = {'Accuracy': 'accuracy', 'roc_auc': 'roc_auc'}                                                                                                                
    
    # SciKit Gradient Boosting - Cross Val
    start_ts=time.time()
    gbclf=GradientBoostingClassifier(n_estimators=100, loss='deviance',learning_rate=0.1, max_depth=3, min_samples_split=3,random_state=rand_st)
    scores = cross_validate(gbclf,data_np,target_np,scoring=scorers,cv=5)

    scores_Acc = scores['test_Accuracy']                                                                                                                                    
    print("Gradient Boosting Accuracy: %0.2f (+/- %0.2f)" % (scores_Acc.mean(), scores_Acc.std() * 2))                                                                                                    
    scores_AUC= scores['test_roc_auc']                                                                     # Only works with binary classes, not multiclass                  
    print("Gradient Boosting Accuracy AUC: %0.2f (+/- %0.2f)" % (scores_AUC.mean(), scores_AUC.std() * 2))                           
    print("CV Runtime:", time.time()-start_ts)


    # SciKit Ada Boosting - Cross Val
    start_ts=time.time()
    adaclf = AdaBoostClassifier(n_estimators=100,base_estimator=None,learning_rate=0.1,random_state=rand_st)
    scores = cross_validate(adaclf,data_np,target_np,scoring=scorers,cv=5)

    scores_Acc = scores['test_Accuracy']                                                                                                                                    
    print("AdaBoost Acc: %0.2f (+/- %0.2f)" % (scores_Acc.mean(), scores_Acc.std() * 2))                                                                                                    
    scores_AUC= scores['test_roc_auc']                                                                     # Only works with binary classes, not multiclass                  
    print("AdaBoost AUC: %0.2f (+/- %0.2f)" % (scores_AUC.mean(), scores_AUC.std() * 2))                           
    print("CV Runtime:", time.time()-start_ts)


    # SciKit Neural Network - Cross Val
    start_ts=time.time()
    nnclf = MLPClassifier(activation='logistic',solver='adam',alpha=0.0001,hidden_layer_sizes=(10,),max_iter=10000,random_state=rand_st)
    scores = cross_validate(nnclf,data_np,target_np,scoring=scorers,cv=5)

    scores_Acc = scores['test_Accuracy']                                                                                                                                    
    print("Neural Network Accuracy: %0.2f (+/- %0.2f)" % (scores_Acc.mean(), scores_Acc.std() * 2))                                                                                                    
    scores_AUC= scores['test_roc_auc']                                                                     # Only works with binary classes, not multiclass                  
    print("Neural Network AUC: %0.2f (+/- %0.2f)" % (scores_AUC.mean(), scores_AUC.std() * 2))                           
    print("CV Runtime:", time.time()-start_ts)
