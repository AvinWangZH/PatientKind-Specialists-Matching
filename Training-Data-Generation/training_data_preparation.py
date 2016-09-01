'''
This function uses files generated by other functions:
'author_omimID_mat_coo.p'   by OMIMScraping.py
'gene_reviews_training_dict.json'  by gene_reviews_data_processing.py
'omim_dict_final.json'  by omim_scraping.py
'disease_list_for_learning.json'  by omim_scraping.py
'author_list_for_learning.json'  by omim_scraping.py
'''
import pickle
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager
from sklearn import svm
from collections import Counter
import logging
import re

def get_author_list(training_dict):   
    author_list = []
    for i in training_dict:
        for j in training_dict[i]['authors']:
            if j not in author_list:
                author_list.append(j)
    return author_list    

def get_omimID_list(training_dict):
    omimID_list = []
    for i in training_dict:
        omimID_list.append(i)
    return omimID_list

def get_omimID_author_label(author_list, omimID_list, training_dict):
    #The first layer of matriz is label 0 or 1. 0 means not expert, 1 means expert
    mat = np.zeros((len(author_list), len(omimID_list)))
    for i in range(len(author_list)):
        for j in range(len(omimID_list)):
            if author_list[i] in training_dict[omimID_list[j]]['authors'].keys():
                mat[i][j] = 1
    return mat

def get_feature_mat(author_list, omimID_list, training_dict, author_omimID_full_mat):
    mat = np.zeros((len(author_list), len(omimID_list), 3))
    
    # Feature #1: number of publications of each author on each disease
    for i in range(len(author_list)):
        for j in range(len(omimID_list)):
            if author_list[i] in training_dict[omimID_list[j]]['authors'].keys():
                mat[i][j][0] = training_dict[omimID_list[j]]['authors'][author_list[i]]
    '''    
    for author_i, author in enumerate(author_list):
        for omim_i, omim_id in enumerate(omimID_list):
            pub_counts = training_dict[omim_id]['authors']
            if author in pub_counts:
                mat[author_i][omim_i][0] = pub_counts[author] 
    '''
    #Remove the duplicate names and redundant content
                
    # Feature #2: number of publications the author has in total
    for i in range(len(author_list)):
        print(i)
        author_index = full_author_list.index(author_list[i])
        mat[i][0][1] =  author_omimID_full_mat.getrow(author_index).sum()  
    for i in range(len(author_list)):
        for j in range(len(omimID_list)):
            mat[i][j][1] = mat[i][0][1]
            
    # Feature #3: number of disease the author published papers
    for i in range(len(author_list)):
        print(i)
        author_index = full_author_list.index(author_list[i])
        count = 0
        for j in author_omimID_full_mat.getrow(author_index).toarray()[0]:
            if j != 0:
                count += 1
        mat[i][0][2] = count
    for i in range(len(author_list)):
        for j in range(len(omimID_list)):
            mat[i][j][2] = mat[i][0][2]    
    return mat

def get_num_experts(mat):
    count = 0
    for i in range(mat.shape[0]):
        for j in range(mat[i].size):
            if mat[i][j] != 0: 
                count += 1    
    return count

def get_training_data(gene_review_training_dict, omim_dict):
    training_data_dict = {} #key: OMIM Ids, value: training data
    other_data_dict = {} #key: OMIM Ids, value: total # of pub for that disease
    #count every authors publications in related OMIM ids
    for omim_id in gene_review_training_dict:
        full_author_list = []
        total_num_pub = len(omim_dict[omim_id]['pubList'])
        for pubmed_id in omim_dict[omim_id]['pubList']:
            full_author_list.extend(omim_dict[omim_id]['pubList'][pubmed_id]['authors'])
        
        full_author_pub_count = dict(Counter(full_author_list))
        other_data_dict[omim_id] = total_num_pub
        training_data_dict[omim_id] = full_author_pub_count
    #start build features, feature 1: number of publications on the specific disease
    for omim_id in training_data_dict:
        for author in training_data_dict[omim_id]:
            training_data_dict[omim_id][author] = [training_data_dict[omim_id][author]]
    
    #feature 2: add number of authors who published in the OMIM id
    for omim_id in training_data_dict:
        author_num = len(training_data_dict[omim_id])
        for author in training_data_dict[omim_id]:
            training_data_dict[omim_id][author].append(author_num)
    
    
    #feature 3&4: add total publication in the OMIM id and percentage of author pub in that OMIM id pub pool
    for omim_id in training_data_dict:
        for author in training_data_dict[omim_id]:
            personal_pub = training_data_dict[omim_id][author][0]
            training_data_dict[omim_id][author].append(other_data_dict[omim_id])
            training_data_dict[omim_id][author].append(personal_pub/other_data_dict[omim_id])
    
    
    #feature 5: add normalized publication number for each author (with 0 std, nan instead --> label as 0)
    for omim_id in training_data_dict:
        pub_num_list = []
        for author in training_data_dict[omim_id]:
            pub_num_list.append(training_data_dict[omim_id][author][0])
        pub_num_arr = np.array(pub_num_list)
        mean = np.mean(pub_num_arr)
        std = np.std(pub_num_arr)
        for author in training_data_dict[omim_id]:
            if std != 0:
                training_data_dict[omim_id][author].append((training_data_dict[omim_id][author][0]-mean)/std)
            else:
                training_data_dict[omim_id][author].append(0)
            
    #feature 6: num of disease the author has publications on
    count = 0
    for omim_id in training_data_dict:
        for author in training_data_dict[omim_id]:
            index = full_author_list_omim.index(author)
            num_disease_with_paper = author_omimID_full_mat.getrow(index).size
            training_data_dict[omim_id][author].append(num_disease_with_paper)
            print(count)
            count += 1
    
    #feature 7&8: number of publications as first author/last author
    for omim_id in training_data_dict:
        first_last_author_dict = {}
        for pub in omim_dict[omim_id]['pubList']:
            if omim_dict[omim_id]['pubList'][pub]['authors'] != []:
                first_author = omim_dict[omim_id]['pubList'][pub]['authors'][0]
                last_author = omim_dict[omim_id]['pubList'][pub]['authors'][-1]
                if first_author in first_last_author_dict:
                    first_last_author_dict[first_author]['count_first'] += 1
                else:
                    first_last_author_dict[first_author] = {'count_first': 1, 'count_last': 0}
                    
                if last_author in first_last_author_dict:
                    first_last_author_dict[last_author]['count_last'] += 1
                else:
                    first_last_author_dict[last_author] = {'count_first': 0, 'count_last': 1} 
                    
        for author in training_data_dict[omim_id]:
            if author not in first_last_author_dict:
                training_data_dict[omim_id][author].extend([0, 0])
            else:
                first_last_count = first_last_author_dict[author]
                training_data_dict[omim_id][author].append(first_last_count['count_first'])
                training_data_dict[omim_id][author].append(first_last_count['count_last'])
    
    #feature 9&10&11: number of publications in 3 years, 5 years and 10 years
    for omim_id in training_data_dict:
        pub_year_count = {}
        for author in training_data_dict[omim_id]:
            pub_year_count[author] = [0, 0, 0]
            
        for pub in omim_dict[omim_id]['pubList']:
            if 'Note' in omim_dict[omim_id]['pubList'][pub]['journal']:
                #print(omim_dict[omim_id]['pubList'][pub]['journal'])
                index = omim_dict[omim_id]['pubList'][pub]['journal'].index('Note')
                pub_year = int(omim_dict[omim_id]['pubList'][pub]['journal'][index-6:index-2])
            elif 'Fig' in omim_dict[omim_id]['pubList'][pub]['journal']:
                index = omim_dict[omim_id]['pubList'][pub]['journal'].index('Fig')
                pub_year = int(omim_dict[omim_id]['pubList'][pub]['journal'][index-6:index-2])
            else:
                #print(omim_dict[omim_id]['pubList'][pub]['journal'])
                pub_year = int(omim_dict[omim_id]['pubList'][pub]['journal'].replace(' .', '')[-5:-1])
                
            if 2016 - pub_year < 3:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_year_count[author][0] += 1
                
            elif 2016 - pub_year < 5:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_year_count[author][1] += 1                
                
            elif 2016 - pub_year < 10:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_year_count[author][2] += 1     
    
        for author in training_data_dict[omim_id]:
            print(pub_year_count[author])
            training_data_dict[omim_id][author].extend(pub_year_count[author]) 
            
    #feature 12&13&14: number of publications in top 3, 5, 10 Bio venues
    source_re = re.compile(r'((?:[a-zA-Z\s\.]+)+).+(\d{4}).*')  
    bio_journal_list = [ 'New Eng. J. Med.', 'Lancet', 'Cell', 'Proc. Nat. Acad. Sci.', 'J. Clin. Oncol.', 'JAMA', 'Nature Genet.', 'Circulation', 'J. Am. Coll. Cardiol.', 'PLoS One']
    for omim_id in training_data_dict:
        pub_journal_count = {}
        for author in training_data_dict[omim_id]:
            pub_journal_count[author] = [0, 0, 0]
        for pub in omim_dict[omim_id]['pubList']:
            string = omim_dict[omim_id]['pubList'][pub]['journal']
            match = source_re.match(string) 
            journal = match.group(1).strip()
            if journal in bio_journal_list[:3]:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_journal_count[author][0] += 1
            elif journal in bio_journal_list[3:5]:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_journal_count[author][1] += 1                
            elif journal in bio_journal_list[5:]:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_journal_count[author][2] += 1 
        for author in training_data_dict[omim_id]:
            print(pub_journal_count[author])
            training_data_dict[omim_id][author].extend(pub_journal_count[author])             
  
    #feature 15&16&17: number of publications in top 3, 5, 10 Gene venues
    genet_journal_list = ['Nature Genet.', 'Nature Rev. Genet.', 'PLoS Genet.', 'Genome Res.', 'Oncogene', 'Genome Biol.', 'Am. J. Hum Genet.', 'Hum. Molec. Genet.', 'BMC Genet.', 'Genetics']  
    
    for omim_id in training_data_dict:
        pub_journal_count = {}
        for author in training_data_dict[omim_id]:
            pub_journal_count[author] = [0, 0, 0]
        for pub in omim_dict[omim_id]['pubList']:
            string = omim_dict[omim_id]['pubList'][pub]['journal']
            match = source_re.match(string) 
            journal = match.group(1).strip()            
            if journal in genet_journal_list[:3]:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_journal_count[author][0] += 1
            elif journal in genet_journal_list[3:5]:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_journal_count[author][1] += 1                
            elif journal in genet_journal_list[5:]:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_journal_count[author][2] += 1 
        for author in training_data_dict[omim_id]:
            print(pub_journal_count[author])
            training_data_dict[omim_id][author].extend(pub_journal_count[author])      
    
    #feature 18&19: number of publications in Nature or Science
    two_best_journals = ['Nature', 'Science']
    for omim_id in training_data_dict:
        pub_journal_count = {}
        for author in training_data_dict[omim_id]:
            pub_journal_count[author] = [0]
        for pub in omim_dict[omim_id]['pubList']:
            string = omim_dict[omim_id]['pubList'][pub]['journal']
            match = source_re.match(string) 
            journal = match.group(1).strip()            
            if journal in two_best_journals:
                for author in omim_dict[omim_id]['pubList'][pub]['authors']:
                    pub_journal_count[author][0] += 1
        for author in training_data_dict[omim_id]:
            training_data_dict[omim_id][author].extend(pub_journal_count[author])      
    
    #add labels to the training data
    for omim_id in training_data_dict:
        for author in training_data_dict[omim_id]:
            if author in gene_review_training_dict[omim_id]['authors']:
                training_data_dict[omim_id][author] = (training_data_dict[omim_id][author], 1)
            else:
                training_data_dict[omim_id][author] = (training_data_dict[omim_id][author], 0)   
                
    return training_data_dict

def build_positive_testing_set(training_data_dict):
    positive_testing_set = []
    count = 0
    for omim_id in training_data_dict:
        for author in training_data_dict[omim_id]:
            if training_data_dict[omim_id][author][1] == 1:
                temp = training_data_dict[omim_id][author][0] + [author] + [omim_id]
                count += 1
                positive_testing_set.append(temp)
                #logging.warning('{} number of positive examples'.format(count))
    return positive_testing_set
    
def build_negative_set(training_data_dict):
    negative_set = []
    count = 0
    for omim_id in training_data_dict:
        for author in training_data_dict[omim_id]:
            if training_data_dict[omim_id][author][1] != 1:
                temp = training_data_dict[omim_id][author][0] + [author] + [omim_id]
                negative_set.append(temp)
                count += 1
                #logging.warning('{} number of negative examples'.format(count))
    return negative_set


if __name__ == '__main__':
    with open('omim_dict_final.json', 'r') as f2:
        omim_dict = json.load(f2)    
    
    with open('gene_reviews_training_dict.json', 'r') as f3:
        gene_review_training_dict = json.load(f3)
        
    with open('author_omimID_mat_coo.p', 'rb') as f4:
        author_omimID_full_mat = pickle.load(f4)
        
    with open('disease_list_for_learning.json', 'r') as f5:
        full_omimID_list_omim = json.load(f5)    
    
    with open('author_list_for_learning.json', 'r') as f6:
        full_author_list_omim = json.load(f6)  
        
    #used for first time to gathering the data
    training_data_dict = get_training_data(gene_review_training_dict, omim_dict)
    
    #get positive and negative sets
    positive_set = build_positive_testing_set(training_data_dict)
    negative_set = build_negative_set(training_data_dict)