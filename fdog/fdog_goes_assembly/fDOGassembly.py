############################ imports ###########################################
import os

########################### functions ##########################################



def merge_regions(blast_results, cut_off):
    number_regions = 0
    for key in blast_results:
        locations = blast_results[key]
        size_list = len(locations)
        i = 0
        j = 1
        old_size = 0
        while size_list != old_size and i < size_list:
            old_size = size_list
            start = locations[i][0]
            end = locations[i][1]

            print(locations)
            while j < size_list:

                # breakup point? or we have to skip this j
                if (i == j) and (j + 1 < size_list):
                    j+=1
                elif (i == j):
                    break

                if (locations[i][0] < locations[j][0]) and (locations[i][1] > locations[j][0]):
                    # start is between start and end -> merge
                    locations[i][1] = max(locations[j][1], locations[i][1])
                    locations[i][2] = min(locations[j][2], locations[i][2])
                    locations.pop(j)
                    j -= 1
                elif (locations[i][0] < locations[j][1]) and (locations[i][1] > locations[j][1]):
                    #end is between start and end -> merge
                    locations[i][0] = min(locations[j][0], locations[i][0])
                    locations[i][2] = min(locations[j][2], locations[i][2])
                    locations.pop(j)
                    j -= 1
                elif (locations[i][0] > locations[j][1]) and (locations[i][0] - locations[j][1] <= cut_off):
                    # end is not more than cut-off distanced
                    locations[i][0] = locations[j][0]
                    locations[i][2] = min(locations[j][2], locations[i][2])
                    locations.pop(j)
                    j -= 1
                elif (locations[i][1] < locations[j][0] and locations[j][0] - locations[i][1] <= cut_off):
                    # start is not more than cut-off distanced
                    locations[i][0] = locations[j][0]
                    locations[i][2] = min(locations[j][2], locations[i][2])
                    locations.pop(j)
                    j -= 1
                j += 1
                size_list = len(locations)

            i += 1
            j = 0
        number_regions += size_list

    return blast_results, number_regions

def parse_blast(line, blast_results):
    # format blast line:  <contig> <start> <end> <evalue> <score>
    #fomrat dictionary: {node_name: [(<start>,<end>)]}
    #print(line)
    line = line.replace("\n", "")
    line_info = line.split("\t")
    #print(line_info)
    evalue = float(line_info[3])

    #cut off
    if evalue > 0.0001:
        return blast_results, evalue
    #add region to dictionary
    else:
        node_name, start, end = line_info[0], line_info[1], line_info[2]
        if node_name in blast_results:
            list = blast_results[node_name]
            list.append([int(start),int(end), evalue])
            blast_results[node_name] = list
        else:
            blast_results[node_name] = [[int(start),int(end), evalue]]

    return blast_results, evalue



def candidate_regions(cut_off):
    ###################### extracting candidate regions ########################
    # info about output blast http://www.metagenomics.wiki/tools/blast/blastn-output-format-6
    blast_file = open("tmp/blast_results.out", "r")

    evalue = 0
    blast_results = {}
    #parsing blast output
    while True:
        line = blast_file.readline()
        #end of file is reached
        if not line:
            break
        #parsing blast output
        blast_results, evalue = parse_blast(line, blast_results)
        #evalue cut-off
        if not evalue <= 0.00001:
            break
    if blast_results == {}:
        return 1
    else:
        candidate_regions, number_regions = merge_regions(blast_results, cut_off)
        print(candidate_regions, number_regions)



def main():

    ########################### handle user input ##############################

    #user input core_ortholog group
    #have to add an input option

    #core-ortholog group name
    group = "778452"

    #species name assemblie (folder name in assemby folder)
    species_name = "L.pustulata"

    #assembly species_name
    assembly_name = "contigs.fa"

    cut_off = 500


    ########################## paths ###########################################

    #open core_ortholog group
    msa_path = "../data/core_orthologs/" + group +"/"+ group + ".aln"
    hmm_path = "../data/core_orthologs/" + group +"/hmm_dir/"+ group + ".hmm"
    consensus_path = "tmp/" + group + ".con"
    profile_path = "tmp/" + group + ".prfl"
    path_assembly = "../data/assembly_dir/" + species_name + "/" + assembly_name
    augustus_path = "msa2prfl.pl"

    os.system('mkdir tmp')


    #msa = open("../data/core_orthologs/" + group +"/"+ group + ".aln", "r")
    #lines = msa.readlines()
    #msa.close()

    ######################## consensus sequence ################################

    #make a majority-rule consensus seqeunce with the tool hmmemit from hmmer
    print("Building a consensus sequence \n")
    os.system('hmmemit -c -o' + consensus_path + ' ' + hmm_path)
    print("consensus seqeunce is finished\n")

    ######################## block profile #####################################
    print("Building a block profile \n")
    os.system('msa2prfl.pl ' + msa_path + ' --setname=' + group + ' >' + profile_path)
    print("block profile is finished \n")
    ######################## tBLASTn ###########################################

    #database anlegen
    print("creating a blast database \n")
    os.system('makeblastdb -in ' + path_assembly + ' -dbtype nucl -out ' + path_assembly)
    print("database is finished \n")

    #make a tBLASTn search against the new database

    os.system('tblastn -db ' + path_assembly + ' -query ' + consensus_path + ' -outfmt "6 sseqid sstart send evalue bitscore" -out tmp/blast_results.out')

    # parse blast and filter for candiate regions
    regions = candidate_regions(cut_off)


    ################# remove tmp folder ########################################

    #have to be added after program ist finished, maybe use parametere so that the user can turn it off

if __name__ == '__main__':
    main()
