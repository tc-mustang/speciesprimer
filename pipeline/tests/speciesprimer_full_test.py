#!/usr/bin/env python3
# -*- coding: utf-8 -*-

msg = (
"""
Works only in the Docker container!!!
- Start the container
    sudo docker start {Containername}
- Start an interactive terminal in the container
    sudo docker exec -it {Containername} bash
- Start the test in the container terminal
    pytest -vv /home/pipeline/tests/speciesprimer_fulltest.py
"""
)


import os
import sys
import shutil
import pytest
import json
import time
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


BASE_PATH = os.path.abspath(__file__).split("tests")[0]
new_path = os.path.join(BASE_PATH, "bin")
sys.path.append(new_path)

from basicfunctions import HelperFunctions as H
from basicfunctions import GeneralFunctions as G

testfiles_dir = os.path.join(BASE_PATH, "tests", "testfiles")
ref_data = os.path.join(BASE_PATH, "tests", "testfiles", "ref")

confargs = {
    "ignore_qc": False, "mfethreshold": 80, "maxsize": 200,
    "target": "Lactobacillus_curvatus", "nolist": False, "skip_tree": False,
    "blastseqs": 1000, "mfold": -3.0, "mpprimer": -3.5,
    "offline": False,
    "path": os.path.join("/", "home", "primerdesign", "test"),
    "probe": False, "exception": None, "minsize": 70, "skip_download": True,
    "customdb": None, "assemblylevel": ["all"], "qc_gene": ["rRNA"],
    "blastdbv5": False, "intermediate": True, "nontargetlist": ["Lactobacillus sakei"]}

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

@pytest.fixture
def config():
    from speciesprimer import CLIconf
    args = AttrDict(confargs)
    nontargetlist = H.create_non_target_list(args.target)
    config = CLIconf(
            args.minsize, args.maxsize, args.mpprimer, args.exception,
            args.target, args.path, args.intermediate,
            args.qc_gene, args.mfold, args.skip_download,
            args.assemblylevel, nontargetlist,
            args.skip_tree, args.nolist, args.offline,
            args.ignore_qc, args.mfethreshold, args.customdb,
            args.blastseqs, args.probe, args.blastdbv5)

    config.save_config()

    return config

def compare_ref_files(results_dir, ref_dir):

    resfileslist = []
    reffileslist = []

    resrecords = []
    refrecords = []
    def compare_files(resfiles, reffiles):
        resrecords = []
        refrecords = []
        records = SeqIO.parse(resfiles, "fasta")
        for record in records:
            resrecords.append([str(record.id), str(record.seq)])
        records = SeqIO.parse(reffiles, "fasta")
        for record in records:
            refrecords.append([str(record.id), str(record.seq)])

        resrecords.sort()
        refrecords.sort()

        for index, item in enumerate(resrecords):
#            print(item.id, refrecords[index].id)
            assert item[0] == refrecords[index][0]
            assert item[1] == refrecords[index][1]

    if os.path.isdir(results_dir):
        for files in os.listdir(results_dir):
            if not files.endswith(".txt"):
                resfiles = os.path.join(results_dir, files)
                resfileslist.append(resfiles)
        resfileslist.sort()

        for files in resfileslist:
            resrecords.append(files)

        for files in os.listdir(ref_dir):
            if not files.endswith(".txt"):
                reffiles = os.path.join(ref_dir, files)
                reffileslist.append(reffiles)
        reffileslist.sort()

        for files in reffileslist:
            refrecords.append(files)

        for index, item in enumerate(resrecords):
            compare_files(item, refrecords[index])

    else:
        resfiles = os.path.join(results_dir)
        reffiles = os.path.join(ref_dir)
        compare_files(resfiles, reffiles)


def test_CLIconf(config):
    assert config.minsize == confargs['minsize']
    assert config.maxsize == confargs['maxsize']
    assert config.ignore_qc == confargs['ignore_qc']
    assert config.mfethreshold == confargs['mfethreshold']
    assert config.target == confargs['target']
    assert config.nolist == confargs['nolist']
    assert config.skip_tree == confargs['skip_tree']
    assert config.blastseqs == confargs['blastseqs']
    assert config.mfold == confargs['mfold']
    assert config.mpprimer == confargs['mpprimer']
    assert config.offline == confargs['offline']
    assert config.probe == confargs['probe']
    assert config.exception == confargs['exception']
    assert config.customdb == confargs['customdb']
    assert config.skip_download == confargs['skip_download']
    assert config.assemblylevel == confargs['assemblylevel']
    assert config.qc_gene == confargs['qc_gene']
    assert config.blastdbv5 == confargs['blastdbv5']

def test_auto_run_config():
    from speciesprimer import auto_run
    t = os.path.join(BASE_PATH, "tests", "testfiles", "tmp_config.json")
    # Docker only
    tmp_path = os.path.join("/", "home", "pipeline", "tmp_config.json")
    if os.path.isfile(tmp_path):
        os.remove(tmp_path)
    shutil.copy(t, tmp_path)
    targets, conf_from_file, use_configfile = auto_run()

    assert targets == ["Lactobacillus_curvatus"]
    assert use_configfile == True
    for target in targets:
        target = target.capitalize()
        if use_configfile:
            (
                minsize, maxsize, mpprimer, exception, target, path,
                intermediate, qc_gene, mfold, skip_download,
                assemblylevel, skip_tree, nolist,
                offline, ignore_qc, mfethreshold, customdb,
                blastseqs, probe, blastdbv5
            ) = conf_from_file.get_config(target)

    assert minsize == confargs['minsize']
    assert maxsize == confargs['maxsize']
    assert ignore_qc == confargs['ignore_qc']
    assert mfethreshold == confargs['mfethreshold']
    assert target == confargs['target']
    assert nolist == confargs['nolist']
    assert skip_tree == confargs['skip_tree']
    assert blastseqs == confargs['blastseqs']
    assert mfold == confargs['mfold']
    assert mpprimer == confargs['mpprimer']
    assert offline == confargs['offline']
    assert probe == confargs['probe']
    assert exception == confargs['exception']
    assert customdb == confargs['customdb']
    assert skip_download == confargs['skip_download']
    assert assemblylevel == confargs['assemblylevel']
    assert qc_gene == confargs['qc_gene']
    assert blastdbv5 == confargs['blastdbv5']

def clean_before_tests(config):
    shutil.rmtree(os.path.join(config.path, config.target))

def test_DataCollection(config):
    clean_before_tests(config)
    from speciesprimer import DataCollection
    DC = DataCollection(config)

    def test_get_email_from_config(config):
        email = DC.get_email_for_Entrez()
        assert email == "biologger@protonmail.com"
        return email

    def internet_connection():
        from urllib.request import urlopen
        try:
            response = urlopen('https://www.google.com/', timeout=5)
            return True
        except:
            print("No internet connection!!! Skip online tests")
            return False

    def test_get_taxid(config):
        email = DC.get_email_for_Entrez()
        taxid, email = DC.get_taxid(config.target)
        assert taxid == '28038'
        return taxid

    def test_ncbi_download(taxid, email):
        DC.get_ncbi_links(taxid, email, 1)
        DC.ncbi_download()
        # clean up
        fna = os.path.join(config.path, config.target, "genomic_fna")
        shutil.rmtree(fna)
        G.create_directory(fna)

    def test_prokka_is_installed():
        cmd = "prokka --citation"
        lines = G.read_shelloutput(cmd, printcmd=False, logcmd=False, printoption=False)
        assert lines[0] == "If you use Prokka in your work, please cite:"

    def prepare_prokka(config):
        testdir = os.path.join(BASE_PATH, "tests", "testfiles")
        targetdir = os.path.join(config.path, config.target)
        fileformat = ["fna", "gff", "ffn"]
        for fo in fileformat:
            for files in os.listdir(testdir):
                if files.endswith("."+fo):
                    fromfile = os.path.join(testdir, files)
                    tofile =  os.path.join(targetdir, fo + "_files", files)
                    shutil.copy(fromfile, tofile)
                    if fo == "fna":
                        tofile = os.path.join(targetdir, "genomic_fna", files)
                        shutil.copy(fromfile, tofile)

    def test_run_prokka():
        annotation_dirs, annotated = DC.run_prokka()
        assert annotated == ["GCF_004088235v1"]
        DC.copy_genome_files()

    def remove_prokka_testfiles():
        fileformat = ["fna", "gff", "ffn"]
        targetdir = os.path.join(config.path, config.target)
        for form in fileformat:
            dirpath = os.path.join(targetdir, form + "_files")
            if os.path.isdir(dirpath):
                shutil.rmtree(dirpath)


    email = test_get_email_from_config(config)
    DC.prepare_dirs()
    if internet_connection():
        taxid = test_get_taxid(config)
        test_ncbi_download(taxid, email)
    else:
        G.create_directory(DC.gff_dir)
        G.create_directory(DC.ffn_dir)
        G.create_directory(DC.fna_dir)
    test_prokka_is_installed()
    prepare_prokka(config)
    test_run_prokka()
    remove_prokka_testfiles()
    G.create_directory(DC.gff_dir)
    G.create_directory(DC.ffn_dir)
    G.create_directory(DC.fna_dir)

def test_prokka_and_roary(config):
    from speciesprimer import DataCollection
    from speciesprimer import PangenomeAnalysis
    genomic_dir = os.path.join(config.path, config.target, "genomic_fna")

    def remove_prokka_testfiles():
        fileformat = ["fna", "gff", "ffn"]
        targetdir = os.path.join(config.path, config.target)
        for form in fileformat:
            dirpath = os.path.join(targetdir, form + "_files")
            if os.path.isdir(dirpath):
                shutil.rmtree(dirpath)

    def prepare_files():
        if os.path.isdir(genomic_dir):
            shutil.rmtree(genomic_dir)
        G.create_directory(genomic_dir)
        files = ["GCF_001981925v1_20190923.ffn", "GCF_003410375v1_20190923.ffn"]
        ffn_files_dir = os.path.join(testfiles_dir, "ffn_files")

        for filename in files:
            filepath = os.path.join(ffn_files_dir, filename)
            sequences = []
            with open(filepath) as f:
                records = list(SeqIO.parse(f, "fasta"))
            for record in records:
                seq = str(record.seq)
                sequences.append(seq)
            newfilename = ".".join(filename.split(".ffn")[0].split("v")) + "_genomic.fna"
            outpath = os.path.join(genomic_dir, newfilename)
            mockfna = SeqRecord(
                Seq("".join(sequences)),
                id="MOCK_" + filename.split("_")[1],
                name="MOCK_" + filename.split("_")[1],
                description=" ".join(config.target.split("_")))
            with open(outpath, "w") as o:
                SeqIO.write(mockfna, o, "fasta")

    prepare_files()
    DC = DataCollection(config)
    PA = PangenomeAnalysis(config)
    DC.collect()
    today = time.strftime("%Y%m%d", time.localtime())
    dirnames = ["GCF_001981925v1_" + today, "GCF_003410375v1_" + today]
    PA.run_pangenome_analysis()

    for dirname in dirnames:
        dirpath = os.path.join(PA.target_dir, dirname)
        filelist = []
        for files in os.listdir(dirpath):
            filelist.append(files)

        assert len(filelist) == 12
        shutil.rmtree(dirpath)

    filenames = ["gene_presence_absence.csv", "Lb_curva_tree.nwk"]
    for filename in filenames:
        filepath = os.path.join(PA.pangenome_dir, filename)
        assert os.path.isfile(filepath) == True
        assert os.stat(filepath).st_size > 0

    remove_prokka_testfiles()

    if os.path.isdir(PA.pangenome_dir):
        shutil.rmtree(PA.pangenome_dir)

    G.create_directory(DC.gff_dir)
    G.create_directory(DC.ffn_dir)
    G.create_directory(DC.fna_dir)


def test_QualityControl(config):
    testdir = os.path.join(BASE_PATH, "tests", "testfiles")
    tmpdir = os.path.join(BASE_PATH, "tests", "tmp")
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    targetdir = os.path.join(config.path, config.target)
    config.blastdbv5 = False
    qc_gene = config.qc_gene[0]
    G.create_directory(tmpdir)
    config.customdb = os.path.join(tmpdir, "customdb.fas")
    genomic_dir = os.path.join(targetdir, "genomic_fna")
    if os.path.isdir(genomic_dir):
        shutil.rmtree(genomic_dir)
    G.create_directory(genomic_dir)
    fromfile = os.path.join(
            testdir, "GCF_004088235v1_20191001.fna")
    tofile = os.path.join(
            genomic_dir, "GCF_004088235v1_20191001.fna")
    shutil.copy(fromfile, tofile)

    def create_customblastdb():
        infile = os.path.join(testdir, "customdb.fas")
        cmd = [
            "makeblastdb", "-in", infile, "-parse_seqids", "-title",
            "mock16SDB", "-dbtype", "nucl", "-out", config.customdb]
        G.run_subprocess(
            cmd, printcmd=False, logcmd=False, log=False, printoption=False)

    from speciesprimer import QualityControl
    QC = QualityControl(config)

    def make_duplicate(filename):
        lines = []
        with open(filename, "r") as f:
            for line in f:
                if "v1" in line:
                    line = "v2".join(line.split("v1"))
                    lines.append(line)
                else:
                    lines.append(line)

        with open(filename, "w") as f:
            for line in lines:
                f.write(line)


    def prepare_QC_testfiles(config):
        # GCF_004088235v1_20191001
        testcases = ["004088235v1_20191001", "maxcontigs_date", "noseq_date", "duplicate"]
        fileformat = ["fna", "gff", "ffn"]
        for testcase in testcases:
            for fo in fileformat:
                for files in os.listdir(testdir):
                    if files.endswith(testcases[0] + "."+fo):
                        fromfile = os.path.join(testdir, files)
                        if testcase == "duplicate":
                            files = "v2".join(files.split("v1"))
                            tofile = os.path.join(
                                targetdir, fo + "_files", files)
                            shutil.copy(fromfile, tofile)
                            make_duplicate(tofile)
                        else:
                            tofile =  os.path.join(
                                targetdir, fo + "_files",
                                "GCF_" + testcase + "." + fo)
                            shutil.copy(fromfile, tofile)

        def make_maxcontigs():
            name = "GCF_maxcontigs_date.fna"
            filepath = os.path.join(targetdir, "fna_files", name)
            nonsense = ">nonsense_contig\nATTAG\n"
            with open(filepath, "w") as f:
                for i in range(0,500):
                    f.write(nonsense)

        def remove_qc_seq():
            keeplines = []
            name = "GCF_noseq_date.ffn"
            filepath = os.path.join(targetdir, "ffn_files", name)
            with open(filepath, "r") as f:
                for line in f:
                    keeplines.append(line)

            for gene in QC.searchdict.values():
                for index, line in enumerate(keeplines):
                    if gene in line:
                        del keeplines[index]

            with open(filepath, "w") as f:
                for line in keeplines:
                    f.write(line)

        make_maxcontigs()
        remove_qc_seq()


    prepare_QC_testfiles(config)
    create_customblastdb()

    def prepare_GI_list():
        filepath = os.path.join(QC.config_dir, "NO_Blast.gi")
        with open(filepath, "w") as f:
            f.write("1231231231")

    def remove_GI_list():
        filepath = os.path.join(QC.config_dir, "NO_Blast.gi")
        if os.path.isfile(filepath):
            os.remove(filepath)

    # test without GI list QC should fail
    def test_get_excluded_gis():
        remove_GI_list()
        excluded_gis = QC.get_excluded_gis()
        assert excluded_gis == []
        prepare_GI_list()
        excluded_gis = QC.get_excluded_gis()
        assert excluded_gis == ["1231231231"]
        remove_GI_list()
        excluded_gis = QC.get_excluded_gis()
        assert excluded_gis == []

    def test_search_qc_gene():
        gff = []
        for files in os.listdir(QC.gff_dir):
            if files not in gff:
                gff.append(files)
        for file_name in gff:
            QC.search_qc_gene(file_name, qc_gene)
        assert len(QC.qc_gene_search) == 12
        return gff

    def test_count_contigs(gff_list, contiglimit):
        gff_list = QC.count_contigs(gff_list, contiglimit)
        gff_list.sort()
        assert gff_list == [
                'GCF_004088235v1_20191001.gff',
                'GCF_004088235v2_20191001.gff',
                'GCF_noseq_date.gff']

        return gff_list

    def test_identify_duplicates(gff_list):
        gff_list = QC.identify_duplicates(gff_list)
        gff_list.sort()
        assert gff_list == [
            'GCF_004088235v2_20191001.gff',
            'GCF_noseq_date.gff']
        return gff_list

    def test_check_no_sequence(qc_gene, gff):
        ffn = QC.check_no_sequence(qc_gene, gff)
        assert ffn == ['GCF_004088235v2_20191001.ffn']
        qc_gene = "tuf"
        ffn = QC.check_no_sequence(qc_gene, gff)
        assert ffn == ['GCF_004088235v2_20191001.ffn']

        for files in os.listdir(QC.ffn_dir):
            if files in ffn:
                if files not in QC.ffn_list:
                        QC.ffn_list.append(files)
        assert len(QC.ffn_list) == 1

    def test_choose_sequence(qc_gene):
        qc_dir = os.path.join(QC.target_dir, qc_gene + "_QC")
        G.create_directory(qc_dir)
        qc_seqs = QC.choose_sequence(qc_gene)
        assert len(qc_seqs) == 1
        assert len(qc_seqs[0]) == 2
        # these values changed due to removal of fasta style ">" and new line
        assert len(qc_seqs[0][0]) == 21
        assert len(qc_seqs[0][1]) == 1568
        return qc_seqs

    def qc_blast(qc_gene):
        from speciesprimer import Blast
        from speciesprimer import BlastPrep
        qc_dir = os.path.join(QC.target_dir, qc_gene + "_QC")
        use_cores, inputseqs = BlastPrep(
                        qc_dir, qc_seqs, qc_gene,
                        QC.config.blastseqs).run_blastprep()
        Blast(
            QC.config, qc_dir, "quality_control"
            ).run_blast(qc_gene, use_cores)

    def test_qc_blast_parser(gi_list=False):
        passed = QC.qc_blast_parser(qc_gene)
        if gi_list is True:
            assert passed == [[
                'GCF_004088235v2_00210', '343201711',
                'NR_042437', 'Lactobacillus curvatus',
                'Lactobacillus curvatus', 'passed QC']]
        else:
            assert passed == []

    def test_remove_qc_failures():
        delete = QC.remove_qc_failures(qc_gene)
        fna_files = os.path.join(QC.ex_dir, "fna_files")
        genomic_files = os.path.join(QC.ex_dir, "genomic_fna")
        sumfile = os.path.join(QC.ex_dir, "excluded_list.txt")
        fna = []
        genomic = []
        sumf = []
        for files in os.listdir(fna_files):
            fna.append(files)
        for files in os.listdir(genomic_files):
            genomic.append(files)
        with open(sumfile) as f:
            for line in f:
                sumf.append(line.strip())
        delete.sort()
        assert delete == ['GCF_004088235v1', 'GCF_maxcontigs', 'GCF_noseq']
        fna.sort()
        assert fna == [
            'GCF_004088235v1_20191001.fna',
            'GCF_maxcontigs_date.fna',
            'GCF_noseq_date.fna']
        assert genomic == ['GCF_004088235v1_20191001.fna']
        assert sumf == ['GCF_noseq', 'GCF_maxcontigs', 'GCF_004088235v1']

    test_get_excluded_gis()
    gff_list = test_search_qc_gene()
    gff_list = test_count_contigs(gff_list, QC.contiglimit)
    gff = test_identify_duplicates(gff_list)
    ffn_list = test_check_no_sequence(qc_gene, gff)
    qc_seqs = test_choose_sequence(qc_gene)
    qc_blast(qc_gene)
    test_qc_blast_parser()
    if os.path.isdir(QC.ex_dir):
        shutil.rmtree(QC.ex_dir)
    # Remove Fake species by GI
    QC = QualityControl(config)
    prepare_QC_testfiles(config)
    prepare_GI_list()
    gff_list = test_search_qc_gene()
    gff_list = test_count_contigs(gff_list, QC.contiglimit)
    gff = test_identify_duplicates(gff_list)
    ffn_list = test_check_no_sequence(qc_gene, gff)
    qc_seqs = test_choose_sequence(qc_gene)
    qc_blast(qc_gene)
    test_qc_blast_parser(gi_list=True)
    test_remove_qc_failures()
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    if os.path.isdir(QC.ex_dir):
        shutil.rmtree(QC.ex_dir)

def test_skip_pangenome_analysis(config):
    from speciesprimer import PangenomeAnalysis
    PA = PangenomeAnalysis(config)
    G.create_directory(PA.pangenome_dir)
    fromfile = os.path.join(testfiles_dir, "gene_presence_absence.csv")
    tofile = os.path.join(PA.pangenome_dir, "gene_presence_absence.csv")
    if os.path.isfile(tofile):
        os.remove(tofile)
    shutil.copy(fromfile, tofile)
    exitstat = PA.run_pangenome_analysis()
    assert exitstat == 2

def test_CoreGenes(config):
    from speciesprimer import CoreGenes
    CG = CoreGenes(config)
    def prepare_tests():
        if os.path.isdir(CG.ffn_dir):
            shutil.rmtree(CG.ffn_dir)
        new_ffn_dir = os.path.join(testfiles_dir, "ffn_files")
        shutil.copytree(new_ffn_dir, CG.ffn_dir)
        if os.path.isdir(CG.gff_dir):
            shutil.rmtree(CG.gff_dir)
        new_gff_dir = os.path.join(testfiles_dir, "gff_files")
        shutil.copytree(new_gff_dir, CG.gff_dir)

    def test_coregene_extract(config):

        G.create_directory(CG.results_dir)
        fasta_dir = os.path.join(CG.results_dir, "fasta")
        G.create_directory(fasta_dir)
        CG.run_CoreGenes()
        ref_dir = os.path.join(ref_data, "fasta")
        fasta_dir = os.path.join(CG.results_dir, "fasta")
        compare_ref_files(fasta_dir, ref_dir)

    prepare_tests()
    test_coregene_extract(config)
#
def test_CoreGeneSequences(config):
    from speciesprimer import CoreGeneSequences
    from speciesprimer import BlastParser
    tmpdir = os.path.join(BASE_PATH, "tests", "tmp")
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    config.customdb = os.path.join(tmpdir, "customdb.fas")
    config.blastdbv5 = False
    CGS = CoreGeneSequences(config)


    def test_seq_alignments():
        # skip this test because of variation in alignments
#        CGS.seq_alignments()
#        results_dir = CGS.alignments_dir
        ref_dir = os.path.join(ref_data, "alignments")
#        compare_ref_files(results_dir, ref_dir)
        shutil.copytree(ref_dir, CGS.alignments_dir)
#
    def test_seq_consenus():
        CGS.seq_consensus()
        ref_dir = os.path.join(ref_data, "consensus")
        results_dir = CGS.consensus_dir
        compare_ref_files(results_dir, ref_dir)

    def test_conserved_seqs():
        cons_summary = os.path.join(
            CGS.consensus_dir, "consensus_summary.txt")
        with open(cons_summary, "w") as f:
            f.write("")
        conserved_sequences = CGS.conserved_seqs()
        ref_file = os.path.join(ref_data, "conserved_seqs.fas")
        assert conserved_sequences == 1
        os.remove(cons_summary)
        CGS.conserved_seqs()
        result_file = os.path.join(CGS.blast_dir, "Lb_curva_conserved")
        compare_ref_files(result_file, ref_file)

    def create_mockdict():
        ref_file = os.path.join(ref_data, "conserved_seqs.fas")
        ref_dataset = []
        with open(ref_file, "r") as f:
                datapoint = []
                for index, line in enumerate(f):
                    if index % 2 == 0:
                        datapoint.append(line.split(">")[1].strip())
                    else:
                        datapoint.append(line.strip())
                        ref_dataset.append(datapoint)
                        datapoint = []
        tmp_dict = {}
        for item in ref_dataset:
            tmp_dict.update({item[0]: item[1]})

        return tmp_dict

    def test_noconservedseqs():
        sakei = []
        with open(os.path.join(CGS.blast_dir, "nontargethits.json")) as f:
            for line in f:
                non_dict = json.loads(line)
        for key in non_dict.keys():
            try:
                newval = non_dict[key]["Lactobacillus sakei"]["main_id"]
                if not newval in sakei:
                    sakei.append(newval)
            except KeyError:
                pass
        for key in non_dict.keys():
            for i, item in enumerate(sakei):
                try:
                    if not item == non_dict[key]["Lactobacillus sakei"]["main_id"]:
                        non_dict[key].update(
                            {
                                "Lactobacillus sakei_" + str(i + 2)
                                : {"main_id": item,
                                   "gi_ids": []}})
                except KeyError:
                    non_dict[key].update(
                        {
                            "Lactobacillus sakei_" + str(i + 2)
                            : {"main_id": item,
                               "gi_ids": []}})
        with open(os.path.join(CGS.blast_dir, "nontargethits.json"), "w") as f:
            f.write(json.dumps(non_dict))


    def test_run_coregeneanalysis(config):
        G.create_directory(tmpdir)
        def create_customblastdb(config):
            infile = os.path.join(testfiles_dir, "conserved_customdb.fas")
            cmd = [
                "makeblastdb", "-in", infile, "-parse_seqids", "-title",
                "mockconservedDB", "-dbtype", "nucl", "-out", config.customdb]
            G.run_subprocess(
                cmd, printcmd=False, logcmd=False, log=False, printoption=False)

        create_customblastdb(config)
        conserved_seq_dict = CGS.run_coregeneanalysis()
        shutil.rmtree(tmpdir)
        return conserved_seq_dict

    test_seq_alignments()
    test_seq_consenus()
    test_conserved_seqs()
    tmp_dict = create_mockdict()
    conserved_seq_dict = test_run_coregeneanalysis(config)
    assert conserved_seq_dict == tmp_dict

    conserved = BlastParser(
            config).run_blastparser(conserved_seq_dict)
    assert conserved == 0
    test_noconservedseqs()
    conserved = BlastParser(
            config).run_blastparser(conserved_seq_dict)
    assert conserved == 1
    nt_file = os.path.join(CGS.blast_dir, "nontargethits.json")
    if os.path.isfile(nt_file):
        os.remove(nt_file)
    conserved_seq_dict = test_run_coregeneanalysis(config)
    conserved = BlastParser(
            config).run_blastparser(conserved_seq_dict)


def test_blastprep(config):
    from speciesprimer import BlastPrep
    testconditions = [[100, 50], [500,10], [1000,5], [2000,3], [5000,1]]
    listlengths = [50*[100], 10*[500], 5*[1000], [1667,1667,1666], [5000]]
    tmpdir = os.path.join(BASE_PATH, "tests", "tmp")
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    G.create_directory(tmpdir)
    input_list = []
    for i in range(0,5000):
        i = i + 1
        elem = ["seq_"+ str(i), i *"A"]
        input_list.append(elem)
    name = "test"
    directory = tmpdir
    for index, [maxpart, dicts] in enumerate(testconditions):
        maxpart, dicts = [maxpart, dicts]
        bp = BlastPrep(directory, input_list, name, maxpartsize=maxpart)
        bp.create_listdict()
        assert len(bp.list_dict) == dicts
        bp.get_equalgroups()
        print("inputlist maxpartsize dicts")
        print(len(input_list), maxpart, dicts,)
        for i, value in enumerate(bp.list_dict.values()):
            assert len(value) == listlengths[index][i]

    bp = BlastPrep(directory, input_list, name, maxpartsize=1000)
    bp.create_listdict()
    bp.get_equalgroups()
    inlist = bp.write_blastinput()
    reflist = []
    rangelist = [5001, 5000, 4999, 4998, 4997]
    for i, r in enumerate(rangelist):
        for x in reversed(range(5-i, r, 5)):
            if not x in reflist:
                reflist.append("seq_" + str(x))
    assert reflist == inlist

def test_BLASTsettings(config):
    import multiprocessing
    from speciesprimer import Blast
    tmpdir = os.path.join(BASE_PATH, "tests", "tmp")
    bl = Blast(config, tmpdir, "test")
    blastfiles = bl.search_blastfiles(tmpdir)
    assert len(blastfiles) == 5
    blastfile = "test.part-0"
    modes = ["quality_control", "conserved", "primer"]

    db_settings = [
        [False, None],
        [True, None],
        [False, os.path.join(tmpdir, "customdb.fas")],
        [True, os.path.join(tmpdir, "customdb_v5.fas")]]
    db_outcome = [
            "nt", "nt_v5",
            os.path.join(tmpdir, "customdb.fas"),
            os.path.join(tmpdir, "customdb_v5.fas")]
    for i, settings in enumerate(db_settings):
        config.blastdbv5 = settings[0]
        config.customdb = settings[1]
        for mode in modes:
            bl = Blast(config, tmpdir, mode)
            cores = cores = multiprocessing.cpu_count()
            cmd = bl.get_blast_cmd(blastfile, blastfile + "_results.xml", cores)
            if mode == "quality_control":
                assert cmd[2] == "megablast"
            elif mode == "conserved":
                assert cmd[2] == "dc-megablast"
            elif mode == "primer":
                assert cmd[2] == "blastn-short"
            else:
                # there should not be any other modes
                assert cmd[2] == "error"
            assert cmd[-1] == db_outcome[i]
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)

#def test_blastparser(config):
#    pass
#    from speciesprimer import BlastParser
#    write_primer3_input(self, selected_seqs, conserved_seq_dict)
    # primer blastparser function
#    create_primerBLAST_DBIDS(self, nonred_dict)

#    get_alignmentdata(self, alignment)


def test_PrimerDesign(config):
    reffile = os.path.join(testfiles_dir, "ref_primer3_summary.json")
    from speciesprimer import PrimerDesign
    pd = PrimerDesign(config)
    G.create_directory(pd.primer_dir)
    pd.run_primer3()
    p3_output = os.path.join(pd.primer_dir, "primer3_output")
    assert os.path.isfile(p3_output) == True
    pd.run_primerdesign()
    with open(reffile) as f:
        for line in f:
            refdict = json.loads(line)
    assert refdict == pd.p3dict

newmockprimer = {
    "mock_1": {
        "Primer_pairs": 2, "template_seq":
        "NNNGGACACTCTTTCCCTACACGACGCTCTTCCGATCTATGGGAAAGAGTGTCCCCCCNNNCTTGTTTACGTGGCGGCGNNN",
        "Primer_pair_0": {
            "primer_P_penalty": 5.913076, "primer_L_TM": 58.15,
            "primer_R_sequence": "CGCCGCCACGTAAACAAG",
            "primer_L_penalty": 2.886877, "primer_R_penalty": 3.007342,
            "template_seq": "NNNGGACACTCTTTCCCTACACGACGCTCTTCCGATCTATGGGAAAGAGTGTCCCCCCNNNCTTGTTTACGTGGCGGCGNNN",
            "amplicon_seq": "GGACACTCTTTCCCTACACGACGCTCTTCCGATCTATGGGAAAGAGTGTCCCCCCNNNCTTGTTTACGTGGCGGCG",
            "primer_L_sequence": "GGACACTCTTTCCCTACACGACGCTCTTCCGATCTATGGGAAAGAGTGTCCCCCC",
            "product_TM": 80.1424, "primer_R_TM": 57.03, "product_size": 82},
        "Primer_pair_1": {
            "primer_P_penalty": 5.913076, "primer_L_TM": 58.15,
            "primer_R_sequence": "CGCCGCCACGTAAACAAG",
            "primer_L_penalty": 2.886877, "primer_R_penalty": 3.007342,
            "amplicon_seq": "GGACACTCTTTCCCTACACGACGCTCTTCCGATCTATGGGAAAGAGTGTCCCCCCNNNCTTGTTTACGTGGCGGCG",
            "primer_L_sequence": "GGACACTCTTTCCCTACACGACGCTCTTCCGATCTATGGGAAAGAGTGTCCCCCC",
            "product_TM": 80.1424, "primer_R_TM": 57.03, "product_size": 82}},
    "mock_9": {
        "Primer_pairs": 1, "template_seq": "NNNCGCAGCAACACACACACGNNNGGGGGGACACTCTTTCCCATAGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTCCNNN",
        "Primer_pair_3":{
            "primer_P_penalty": 2.427616, "primer_L_TM": 59.691,
            "primer_R_sequence": "GGACACTCTTTCCCTACACGACGCTCTTCCGATCTATGGGAAAGAGTGTCCCCCC",
            "primer_L_penalty": 0.345215, "primer_R_penalty": 2.064444,
            "amplicon_seq": "CGCAGCAACACACACACGNNNGGGGGGACACTCTTTCCCATAGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGTCC",
            "primer_L_sequence": "CGCAGCAACACACACACG", "product_TM": 81.2095,
            "primer_R_TM": 60.029, "product_size": 88}},

    "dimer_1": {
            "Primer_pairs": 1, "template_seq": "NNNN",
            "Primer_pair_0":{
            "primer_P_penalty": 2.427616, "primer_L_TM": 59.691,
            "primer_R_sequence": "TTTTTTAAAAAA",
            "primer_L_penalty": 0.345215, "primer_R_penalty": 2.064444,
            "amplicon_seq": "NNNN",
            "primer_L_sequence": "TTTTTTAAAAAA", "product_TM": 81.2095,
            "primer_R_TM": 60.029, "product_size": 88}}}

ref_hairpins = [
            'Lb_curva_mock_1_P0', 'Lb_curva_mock_1_P1',
            'Lb_curva_mock_9_P3']

ref_excluded = [
            'Lb_curva_asnS_2_P1', 'Lb_curva_comFA_2_P3',
            'Lb_curva_comFA_3_P0', 'Lb_curva_comFA_4_P0',
            'Lb_curva_dimer_1_P0', 'Lb_curva_g1243_1_P1',
            'Lb_curva_g1243_1_P5', 'Lb_curva_gshAB_2_P0',
            'Lb_curva_gshAB_2_P3', 'Lb_curva_mock_1_P0',
            'Lb_curva_mock_1_P1', 'Lb_curva_mock_9_P3']

ref_results = [[
        'Lb_curva_asnS_1_P0_F', 'AAACCATGTCGATGAAGAAGTTAAA',
     'Lb_curva_asnS_1_P0_R', 'TGCCATCACGTAATTGGAGGA',
     'AAACCATGTCGATGAAGAAGTTAAAATTGGCGTTTGGTTAACCGACAAACGNTCAAGTGGGAAGATT'
     + 'TCATTCCTCCAATTACGTGATGGCACTGCCTTTTTCCAAGGGGTTGTCGTTAAAAG',
     'AAACCATGTCGATGAAGAAGTTAAAATTGGCGTTTGGTTAACCGACAAACGNTCAAGTGGGAAGATT'
     + 'TCATTCCTCCAATTACGTGATGGCA', 83.54],
     [
         'Lb_curva_asnS_2_P0_F', 'ACAAGAATCAAGTATGTGGGTGAC',
      'Lb_curva_asnS_2_P0_R', 'TGCTGTCACCAATTAATTCGATGT',
      'AAGCCGTTTTCCAATTGGCAAAAGATGTNAAACAAGAATCAAGTATGTGGGTGACAGGGGTCATNC'
      + 'ATGAAGATACTCGTTCACACTTTGGTTATGAAATTGAAATTTCTGACATCGAATTAATTGGTGAC'
      + 'AGCAG', 'ACAAGAATCAAGTATGTGGGTGACAGGGGTCATNCATGAAGATACTCGTTCACACTT'
      + 'TGGTTATGAAATTGAAATTTCTGACATCGAATTAATTGGTGACAGCA', 84.49]]

def test_PrimerQualityControl(config):

    def dbinputfiles():
        filenames = [
            "GCF_004088235v1_20191001.fna",
            "GCF_002224565.1_ASM222456v1_genomic.fna"]
        dbfile = os.path.join(testfiles_dir, "primer_customdb.fas")
        with open(dbfile, "w") as f:
            for filename in filenames:
                filepath = os.path.join(testfiles_dir, filename)
                records = SeqIO.parse(filepath, "fasta")
                for record in records:
                    if record.id == record.description:
                        description = (
                            record.id + " Lactobacillus curvatus strain SRCM103465")
                        record.description = description
                    SeqIO.write(record, f, "fasta")
        return dbfile

    def create_customblastdb(config, infile):
        cmd = [
            "makeblastdb", "-in", infile, "-parse_seqids", "-title",
            "mockconservedDB", "-dbtype", "nucl", "-out", config.customdb]
        G.run_subprocess(
            cmd, printcmd=False, logcmd=False, log=False, printoption=False)

    def get_primer3_dict():
        reffile = os.path.join(testfiles_dir, "ref_primer3_summary.json")
        with open(reffile) as f:
            for line in f:
                primer3dict = json.loads(line)
        return primer3dict

    def test_collect_primer(config):
        pqc = PrimerQualityControl(config, {})
        assert pqc.collect_primer() == 1
        primer3dict = get_primer3_dict()
        primer3dict.update(newmockprimer)
        pqc = PrimerQualityControl(config, primer3dict)
        assert pqc.collect_primer() == 0

    def test_hairpin_check(config):
        if pqc.collect_primer() == 0:
            hairpins = pqc.hairpin_check()
            hairpins.sort()
            assert hairpins == ref_hairpins

    def test_primerdimer_check(config):
        pqc.primerdimer_check(ref_hairpins)
        excluded = pqc.filter_primerdimer()
        excluded.sort()
        assert excluded == ref_excluded

    def test_MFEprimer_DBs(config):
        primerinfos = []
        for primer in pqc.primerlist:
            pp_name = "_".join(primer[0].split("_")[0:-1])
            if pp_name not in ref_excluded:
                primerinfos.append(primer)
        assert len(primerinfos) == 61

        qc_file = os.path.join(testfiles_dir, "Lb_curva_qc_sequences.csv")
        if os.path.isdir(pqc.summ_dir):
            shutil.rmtree(pqc.summ_dir)
        G.create_directory(pqc.summ_dir)
        shutil.copy(qc_file, pqc.summ_dir)
        pqc.prepare_MFEprimer_Dbs(pqc.primerlist)
        dbtype = [
            "template.sequences",
            "Lb_curva.genomic"]
        dbfiles = [
            ".fai",
            ".json",
            ".log",
            ".primerqc",
            ".primerqc.fai"]

        for db in dbtype:
            for end in dbfiles:
                files =  db + end
                print(files)
                filepath = os.path.join(pqc.primer_qc_dir, files)
                assert os.path.isfile(filepath) == True
                assert os.stat(filepath).st_size > 0

    def test_MFEprimer_specificity_check(config):
        os.chdir(pqc.primer_qc_dir)
        primerinfos = []
        for primer in pqc.primerlist:
            pp_name = "_".join(primer[0].split("_")[0:-1])
            if pp_name not in ref_excluded:
                primerinfos.append(primer)
        assert len(primerinfos) == 61

        template_results = G.run_parallel(pqc.MFEprimer_template, primerinfos)
        assembly_input = pqc.write_MFEprimer_results(template_results, "template")
        assert len(assembly_input) == 60

        assembly_results = G.run_parallel(pqc.MFEprimer_assembly, assembly_input)
        nontarget_input = pqc.write_MFEprimer_results(assembly_results, "assembly")
        assert len(nontarget_input) == 57

        pqc.run_primerBLAST(nontarget_input)
        pqc.prepare_nontargetDB()

        os.chdir(pqc.primer_qc_dir)

        nontarget_results = G.run_parallel(
            pqc.MFEprimer_nontarget, nontarget_input)
        specific_primers = pqc.write_MFEprimer_results(
                nontarget_results, "nontarget")
        specific_primers.sort()
        assert specific_primers[0] == ref_results[0]
        assert specific_primers[1] == ref_results[1]
        assert len(specific_primers) == 55

        return specific_primers

    from speciesprimer import PrimerQualityControl
    tmpdir = os.path.join(BASE_PATH, "tests", "tmp")
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    config.customdb = os.path.join(tmpdir, "primer_customdb.fas")
    config.blastdbv5 = False

    primer3dict = get_primer3_dict()
    primer3dict.update(newmockprimer)

    pqc = PrimerQualityControl(config, primer3dict)
    dbfile = dbinputfiles()
    create_customblastdb(config, dbfile)
    G.create_directory(pqc.primer_qc_dir)
    os.chdir(pqc.primer_qc_dir)

    test_collect_primer(config)
    test_hairpin_check(config)
    test_primerdimer_check(config)
    test_MFEprimer_DBs(config)
    specific_primers = test_MFEprimer_specificity_check(config)
    test_mfold = [
            specific_primers[0], specific_primers[1],
            specific_primers[2], specific_primers[46]]
    pqc.mfold_analysis(test_mfold)
    selected_primer, excluded_primer = pqc.mfold_parser()
    selected_primer.sort()
    excluded_primer.sort()
    assert selected_primer == ['Lb_curva_asnS_1_P0', 'Lb_curva_asnS_2_P0']
    assert excluded_primer == ['Lb_curva_comFA_2_P0', 'Lb_curva_gshAB_2_P2']

def test_summary(config):
    total_results = [
        [
            'Lb_curva_comFA_2_P1', 100.0, 1.64, 'comFA_2',
            'TACCAAGCAACAACGCCATG', 59.4, 0.63,
            'ACACACACGCTGCCCATTAG', 60.95, 0.99,
            'None', 'None', 'None', 106, 82.53,
            'TACCAAGCAAC...',
            'TACCAAGCAACAACGCCATGTC...']]

    from speciesprimer import Summary
    su = Summary(config, total_results)
    su.run_summary("normal")
    for files in os.listdir(su.summ_dir):
        print(files)

def test_end(config):
    def remove_test_files(config):
        test = config.path
        shutil.rmtree(test)
        tmp_path = os.path.join("/", "home", "pipeline", "tmp_config.json")
        if os.path.isfile(tmp_path):
            os.remove(tmp_path)
    remove_test_files(config)

if __name__ == "__main__":
    print(msg)