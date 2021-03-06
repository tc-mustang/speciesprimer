#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import render_template, flash, redirect, url_for, send_file
from app import app
from app.forms import LoginForm, StartForm, NewForm, PipeConfig
from app.forms import PipeOptions, DownloadDB
from app.forms import SettingsForm, ChangeSettingsForm, ControlRunForm, DBForm
import os
import time
import json
import subprocess
import traceback
import shutil
import signal
from werkzeug.utils import secure_filename


app_dir = os.path.dirname(os.path.abspath(__file__))
pipe_dir = app_dir.split('gui')[0]
dict_path = os.path.join(pipe_dir, "dictionaries")
tmp_db_path = os.path.join(pipe_dir, 'tmp_config.json')
daemon_path = os.path.join(pipe_dir, "gui", "daemon", "daemonize.py")


@app.errorhandler(OSError)
def handle_OSError(error):
    flash("Please provide your email address")
    return redirect(url_for('login'))


@app.errorhandler(Exception)
def handle_exception(error):
    tb = traceback.format_exc()
    print(tb)
    return render_template("500.html", error=error, tb=tb), 500


def update_tmp_db(update_dict):
    with open(tmp_db_path, 'r') as f:
        for line in f:
            tmp_db = json.loads(line)
    tmp_db.update(update_dict)
    with open(tmp_db_path, 'w') as f:
        f.write(json.dumps(tmp_db))


def start_frontail():
    tmpdir = os.path.join("/", "programs", "tmp")
    if not os.path.isdir(tmpdir):
        try:
            os.makedirs(tmpdir)
        except OSError:
            if not os.path.isdir(tmpdir):
                raise
    today = time.strftime("%Y_%m_%d", time.localtime())
    log_file = os.path.join(
            "/", "primerdesign", "speciesprimer_" + today + ".log")
    pidfile = os.path.join(tmpdir, "frontail.pid")
    if os.path.isfile(pidfile):
        with open(pidfile) as f:
            for line in f:
                pid = line.strip()
        pidint = int(pid)
        if isinstance(pidint, int):
            try:
                os.kill(pidint, signal.SIGTERM)
            except ProcessLookupError:
                pass
        os.remove(pidfile)
    frontail_cmd = [
            "frontail-linux", "-d", "-n", "20", "--pid-path",
            pidfile, log_file]
    subprocess.Popen(frontail_cmd, cwd=pipe_dir)


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if os.path.isfile(tmp_db_path):
        with open(tmp_db_path) as f:
            for line in f:
                tmp_db = json.loads(line)
        try:
            mail = tmp_db['email']
            if '@' and '.' in mail:
                return redirect(url_for('index'))
        except KeyError:
            pass
    if form.validate_on_submit():
        email = form.email.data
        if os.path.isfile(tmp_db_path):
            with open(tmp_db_path) as f:
                for line in f:
                    tmp_db = json.loads(line)
            tmp_db.update({'email': email})
        else:
            tmp_db = {
                'email': email, 'new_run': {
                    'path': '', 'targets': {},
                    'same_settings': False,
                    'change_settings': False}}
        with open(tmp_db_path, 'w') as f:
            f.write(json.dumps(tmp_db))
        flash('Saved E-mail address {}'.format(email))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/login', methods=['GET', 'POST'])
def change_login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        if os.path.isfile(tmp_db_path):
            with open(tmp_db_path) as f:
                for line in f:
                    tmp_db = json.loads(line)
            tmp_db.update({'email': email})
        else:
            tmp_db = {'email': email}
        with open(tmp_db_path, 'w') as f:
            f.write(json.dumps(tmp_db))
        flash('Saved E-mail address {}'.format(email))
        return redirect(url_for('index'))
    return render_template('change_login.html', title='Sign In', form=form)


@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')


@app.route('/new', methods=['GET', 'POST'])
def new():
    form = NewForm()
    if form.validate_on_submit():
        path = form.wd_path.data
        target_species = form.selected_species.data[0].split(',')
        form_dict = {
            'path': path, 'targets': {},
            'same_settings': form.same_setting.data,
            'change_settings': False, 'modus': 'new'}
        for target in list(target_species):
            target = '_'.join(target.strip(' ').split(' '))
            target = target.capitalize()
            form_dict['targets'].update({target: {}})
        update_tmp_db({'new_run': form_dict})
        return redirect(url_for('settings'))
    return render_template('new.html', title='Start Primerdesign', form=form)


@app.route('/continue', methods=['GET', 'POST'])
def search_continue():
    form = StartForm()
    if form.validate_on_submit():
        path = form.search_path.data
        if form.selected_species.data == ['']:
            target_list = None
        else:
            target_list = []
            target_species = form.selected_species.data[0].split(',')
            for target in target_species:
                target = target.strip().capitalize()
                target_list.append(target)
        update_tmp_db({'new_run': {
                "targets": target_list, "path": path, 'modus': 'continue'}})
        if target_list:
            flash(
                "Press Start Primerdesign to search for config files for "
                + " & ".join(target_list))
        else:
            flash(
                "Press Start Primerdesign to search for config files")
        return redirect(url_for('controlrun'))
    return render_template(
                    'continue.html', title='Continue Primerdesign', form=form)


@app.route('/change_settings', methods=['GET', 'POST'])
def change_settings():
    form = ChangeSettingsForm()
    if form.validate_on_submit():
        f = form.targets.data
        filename = secure_filename(f.filename)
        if f and allowed_file(filename):
            for line in f:
                old_settings = json.loads(line.decode("utf-8"))
        else:
            flash('File has to be a config.json file')
            return render_template(
                    'change_settings.html', title='Change settings', form=form)
        path = old_settings['path']
        update_dict = {"new_run": {
            'path': path, 'same_settings': False,
            'change_settings': True, 'modus': 'new',
            'targets': {old_settings['target']: old_settings}}}
        update_tmp_db(update_dict)
        return redirect(url_for('settings'))
    return render_template(
                    'change_settings.html', title='Change settings', form=form)


def check_targets():
    target_list = []
    target_choice_list = []
    with open(tmp_db_path, 'r') as f:
        for line in f:
            tmp_db = json.loads(line)
    if tmp_db['new_run']['change_settings']:
        for key in tmp_db['new_run']['targets']:
            key = key.capitalize()
            target_list.append(key)
    else:
        for key in tmp_db['new_run']['targets']:
            if tmp_db['new_run']['targets'][key] == {}:
                key = key.capitalize()
                target_list.append(key)
        target_list.sort()

    if tmp_db['new_run']["same_settings"]:
        for item in target_list:
            item = item.capitalize()
            target_choice_list.append(' '.join(item.split('_')))
        return target_choice_list, tmp_db

    for item in target_list:
        item = item.capitalize()
        target_choice_list.append((item, ' '.join(item.split('_'))))
    return target_choice_list, tmp_db


def update_db(sub_dict, target, data):
    (
        qc_gene, ignore_qc, skip_download, assemblylevel, skip_tree, exception,
        minsize, maxsize, designprobe, mfold, mpprimer, mfeprimer_threshold,
        offline, customdb, blastseqs, path, blastdbv5, intermediate, nolist
    ) = data
    sub_dict.update({
            'target': target,
            'minsize': minsize, 'maxsize': maxsize, 'mpprimer': mpprimer,
            'exception': exception, 'path': path, 'intermediate': intermediate,
            'qc_gene': qc_gene, 'mfold': mfold, 'skip_download': skip_download,
            'assemblylevel': assemblylevel, 'skip_tree': skip_tree,
            'nolist': nolist, 'offline': offline, 'ignore_qc': ignore_qc,
            'mfethreshold': mfeprimer_threshold, 'customdb': customdb,
            'blastseqs': blastseqs, 'probe': designprobe,
            'blastdbv5': blastdbv5})
    return sub_dict


def reset_settings(form):
    (
        form.qc_gene.data, form.ignore_qc.data, form.skip_download.data,
        form.assemblylevel.data, form.skip_tree.data, form.exception.data,
        form.minsize.data, form.maxsize.data, form.designprobe.data,
        form.mfold.data, form.mpprimer.data, form.mfeprimer_threshold.data,
        form.work_offline.data, form.customdb.data, form.blastseqs.data,
        form.blastdbv5.data, form.intermediate.data, form.nolist.data
    ) = (
        ["rRNA"], False, False,
        ["all"], False, [],
        70, 200, False,
        -3.0, -3.5, 90,
        False, None, 1000,
        False, False, False
    )
    return form


def load_settings(tmp_db):
    for key in tmp_db['new_run']['targets']:
        target = key
    settings = tmp_db['new_run']['targets'][target]
    (
        qc_gene, ignore_qc, skip_download,
        assemblylevel, skip_tree, exception,
        minsize, maxsize, designprobe,
        mfold, mpprimer, mfeprimer_threshold,
        work_offline, customdb, blastseqs,
        change_wd, blastdbv5, intermediate, nolist
    ) = (
        settings["qc_gene"], settings["ignore_qc"], settings["skip_download"],
        settings["assemblylevel"], settings["skip_tree"],
        settings["exception"], settings["minsize"], settings["maxsize"],
        settings["probe"], settings["mfold"], settings["mpprimer"],
        settings["mfethreshold"], settings["offline"], settings["customdb"],
        settings["blastseqs"], settings['path'], settings['blastdbv5'],
        settings["intermediate"], settings['nolist']
    )

    data = {
        "targets": target, "qc_gene": qc_gene, "ignore_qc": ignore_qc,
        "skip_download": skip_download,
        "assemblylevel": assemblylevel, "skip_tree": skip_tree,
        "exception": exception,
        "minsize": minsize, "maxsize": maxsize, "designprobe": designprobe,
        "mfold": mfold, "mpprimer": mpprimer,
        "mfeprimer_threshold": mfeprimer_threshold,
        "work_offline": work_offline, "customdb": customdb,
        "blastseqs": blastseqs,
        "change_wd": change_wd, "blastdbv5": blastdbv5,
        "intermediate": intermediate, "nolist": nolist}
    return data


def get_settings(form):
    (
        qc_gene, ignore_qc, skip_download, assemblylevel, skip_tree, exception,
        minsize, maxsize, designprobe, mfold, mpprimer, mfeprimer_threshold,
        offline, customdb, blastseqs, path, blastdbv5, intermediate, nolist
    ) = (
        form.qc_gene.data, form.ignore_qc.data, form.skip_download.data,
        form.assemblylevel.data, form.skip_tree.data, form.exception.data,
        form.minsize.data, form.maxsize.data, form.designprobe.data,
        form.mfold.data, form.mpprimer.data, form.mfeprimer_threshold.data,
        form.work_offline.data, form.customdb.data, form.blastseqs.data,
        form.change_wd.data, form.blastdbv5.data, form.intermediate.data,
        form.nolist.data
        )
    if offline:
        skip_download = True
        assemblylevel = ['offline']
    if skip_download:
        assemblylevel = ['offline']
    if exception == [""]:
        exception = []
    else:
        while "" in exception:
            exception.remove("")

    if customdb == "":
        customdb = None
    if 'all' in assemblylevel:
        assemblylevel = ['all']
    return (
        qc_gene, ignore_qc, skip_download, assemblylevel, skip_tree, exception,
        minsize, maxsize, designprobe, mfold, mpprimer, mfeprimer_threshold,
        offline, customdb, blastseqs, path, blastdbv5, intermediate, nolist)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    target_choice_list, tmp_db = check_targets()
    if len(target_choice_list) == 0:
        flash("Press Start Primerdesign to start primer design")
        return redirect(url_for('controlrun'))

    if tmp_db['new_run']['same_settings']:
        def_path = tmp_db['new_run']['path']
        form = SettingsForm(change_wd=def_path)
        form.targets.choices = [("All targets", "All targets")]
    elif tmp_db['new_run']['change_settings']:
        try:
            form = SettingsForm(data=load_settings(tmp_db))
            form.targets.choices = target_choice_list
        except KeyError as exc:
            flash(" ".join([
                'Setting not found:', str(exc),
                'maybe you are using an outdated config file']))
            def_path = tmp_db['new_run']['path']
            form = SettingsForm(change_wd=def_path)
            form.targets.choices = target_choice_list
    else:
        def_path = tmp_db['new_run']['path']
        form = SettingsForm(change_wd=def_path)
        form.targets.choices = target_choice_list

    if form.validate_on_submit():
        if form.reset.data is True:
            reset_form = reset_settings(form)
            return render_template(
                            'settings.html', title='Settings for primerdesign',
                            form=reset_form)

        settings_data = get_settings(form)
        if tmp_db['new_run']['same_settings']:
            for target in tmp_db['new_run']['targets']:  # for same settings
                config = tmp_db['new_run']['targets'][target]
                new_config = update_db(config, target, settings_data)
                tmp_db['new_run']['targets'][target].update(new_config)
                with open(tmp_db_path, 'w') as f:
                    f.write(json.dumps(tmp_db))
        else:
            for target in [form.targets.data]:
                config = tmp_db['new_run']['targets'][target]
                new_config = update_db(config, target, settings_data)
                tmp_db['new_run']['targets'][target].update(new_config)
                with open(tmp_db_path, 'w') as f:
                    f.write(json.dumps(tmp_db))

        if tmp_db['new_run']['same_settings']:
            flash(
                'Saved settings for {}'.format(" & ".join(target_choice_list)))
            flash(
                "Press Start Primerdesign to start primer design for "
                + " & ".join(target_choice_list))
            return redirect(url_for('controlrun'))
        if tmp_db['new_run']['change_settings']:
            conf_path = tmp_db['new_run']['targets'][target]['path']
            save_to = os.path.join(conf_path, target, "config", "config.json")
            try:
                with open(save_to, 'w') as f:
                    f.write(json.dumps(new_config))
                flash('Changed settings for {}'.format(
                                                ' '.join(target.split('_'))))
                flash(json.dumps(new_config))
                flash(
                    "Press Start Primerdesign to start primer design for "
                    + ' '.join(target.split('_')))
                return redirect(url_for('controlrun'))
            except FileNotFoundError:
                flash("The selected directory does not exist")
                return redirect(url_for('settings'))

        else:
            flash('Saved settings for {}'.format(' '.join(target.split('_'))))
        flash(json.dumps(new_config, sort_keys=True))
        return redirect(url_for('settings'))

    return render_template(
            'settings.html', title='Settings for primerdesign', form=form)


@app.route('/primerdesign', methods=['GET', 'POST'])
def primerdesign():
    form = PipeOptions()
    if form.validate_on_submit():
        if form.new.data:
            return redirect(url_for('new'))
        if form.search.data:
            return redirect(url_for('search_continue'))
        if form.control.data:
            return redirect(url_for('controlrun'))
        if form.change.data:
            return redirect(url_for('change_settings'))

    return render_template(
            'speciesprimer.html', title='Primerdesign', form=form)


def start_pipeline():
    start_frontail()
    time.sleep(2)
    subprocess.Popen([daemon_path, "start", "100", "SpeciesPrimer"])


def stop_pipeline():
    subprocess.Popen([daemon_path, "stop", "100", "SpeciesPrimer"])


def start_db_download():
    start_frontail()
    time.sleep(2)
    subprocess.Popen([daemon_path, "start", "200", 'GetBlastDB'])


def stop_db_download():
    subprocess.Popen([daemon_path, "stop", "200", 'GetBlastDB'])


@app.route('/dbdownload', methods=['GET', 'POST'])
def dbdownload():
    form = DBForm()
    if form.validate_on_submit():
        if form.submit.data:
            start_db_download()
            flash("Starting DB download")
            time.sleep(1)
        elif form.stop.data:
            stop_db_download()
            flash("Stopping DB download")
    return render_template(
            'dbdownload.html', title='Control BLAST db download', form=form)


def start_updatedb(command):
    start_frontail()
    time.sleep(2)
    subprocess.Popen(command)


def stop_updatedb(command):
    subprocess.Popen(command)


@app.route('/updatedb', methods=['GET', 'POST'])
def updatedb():
    form = DBForm()
    if form.validate_on_submit():
        if form.submit.data:
            command = [daemon_path, "start", "200", "Update_ntDB"]
            start_updatedb(command)
            time.sleep(1)
        elif form.stop.data:
            command = [daemon_path, "stop", "200", "Update_ntDB"]
            stop_updatedb(command)
    return render_template(
            'dbdownload.html', title='Control BLAST db download', form=form)


@app.route('/updatedb_ref', methods=['GET', 'POST'])
def updatedb_ref():
    form = DBForm()
    if form.validate_on_submit():
        if form.submit.data:
            command = [daemon_path, "start", "200", "Update_prokDB"]
            start_updatedb(command)
            flash("Starting DB download")
            time.sleep(1)
        elif form.stop.data:
            command = [daemon_path, "stop", "200", "Update_prokDB"]
            stop_updatedb(command)
            flash("Stopping DB download")
    return render_template(
            'dbdownload.html', title='Control BLAST db download', form=form)


@app.route('/controlrun', methods=['GET', 'POST'])
def controlrun():
    form = ControlRunForm()
    if form.validate_on_submit():
        if form.submit.data:
            start_pipeline()
            flash("Starting primer design")
            time.sleep(1)
        elif form.stop.data:
            stop_pipeline()
            flash("Stopping primer design")
    return render_template('controlrun.html', title='Control runs', form=form)


@app.route('/streamlog', methods=['GET', 'POST'])
def streamlog():
    redirect_url = "http://localhost:9001/"
    return redirect(redirect_url)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = ["json"]
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_bacteria_taxids():
    if os.path.isfile(tmp_db_path):
        with open(tmp_db_path) as f:
            for line in f:
                tmp_db = json.loads(line)
    from Bio import Entrez
    Entrez.tool = "SpeciesPrimer pipeline"
    Entrez.email = tmp_db['email']
    searchtaxid = Entrez.esearch(
            db="taxonomy", term="txid2[orgn]", retmax="500000")
    taxidresult = Entrez.read(searchtaxid)
    taxids = taxidresult["IdList"]
    taxids.sort(key=int)
    filename = os.path.join(dict_path, "2.txids")
    with open(filename, "w") as f:
        for txid in taxids:
            f.write(txid + "\n")


@app.route('/blastdb', methods=['GET', 'POST'])
def blastdb():
    form = DownloadDB()
    if form.validate_on_submit():
        if form.update_blastdb.data is True:
            return redirect(url_for('updatedb'))
        if form.update_refprok.data is True:
            return redirect(url_for('updatedb_ref'))
        if form.get_blastdb.data is True:
            delete = form.delete.data
            db = form.whichdb.data
            update_dict = {'BLAST_DB': {'delete': delete, 'db': db}}
            update_tmp_db(update_dict)
            return redirect(url_for('dbdownload'))
        if form.update_txids.data is True:
            get_bacteria_taxids()
    return render_template(
            'blastdb.html', title='Download nt database', form=form)


@app.route('/pipelineconfig', methods=['GET', 'POST'])
def pipelineconfig():
    form = PipeConfig()
    if form.validate_on_submit():
        upload_data = [
            [form.up_list.data, "species_list.txt"],
            [form.up_abbrev.data, "genus_abbrev.csv"],
            [form.up_p3sett.data, "p3parameters"],
            [form.up_noblast.data, "no_blast.gi"]]
        download_data = [
            [form.down_list.data, "species_list.txt"],
            [form.down_abbrev.data, "genus_abbrev.csv"],
            [form.down_p3sett.data, "p3parameters"],
            [form.down_noblast.data, "no_blast.gi"]]

        reset_data = [
            [form.reset_list.data, "species_list.txt"],
            [form.reset_abbrev.data, "genus_abbrev.csv"],
            [form.reset_p3sett.data, "p3parameters"],
            [form.reset_noblast.data, "no_blast.gi"]]

        for upform in upload_data:
            if upform[0]:
                filename = secure_filename(upform[0].filename)
                if filename:
                    upform[0].save(os.path.join(dict_path, upform[1]))
                    flash("saved " + upform[1])
                else:
                    flash("not a supported file")

        for downform in download_data:
            if downform[0]:
                return send_file(
                        os.path.join(dict_path, downform[1]),
                        as_attachment=True, attachment_filename=downform[1])

        for resform in reset_data:
            if resform[0]:
                old_file = os.path.join(dict_path, resform[1])
                default = os.path.join(dict_path, "default", resform[1])
                shutil.copy(default, old_file)
                flash("Reset " + resform[1])

    return render_template(
            'pipelineconfig.html',
            title='SpeciesPrimer configuration', form=form)


@app.route('/help')
def helppage():
    return render_template('help.html', title='SpeciesPrimer help')


@app.route('/help_pipelineconfig')
def helppipesetup():
    return render_template(
            'help_pipelinesetup.html', title='SpeciesPrimer help')


@app.route('/help_primerdesign')
def helpprimerdesign():
    return render_template(
            'help_primerdesign.html', title='SpeciesPrimer help')


@app.route('/troubleshooting')
def helptroubleshooting():
    return render_template(
            'help_troubleshooting.html', title='SpeciesPrimer help')


@app.route('/docker')
def helpdocker():
    return render_template(
            'help_dockertroubleshooting.html', title='SpeciesPrimer help')


@app.route('/dockersetup')
def helpdockerproxy():
    return render_template('help_dockerproxy.html', title='SpeciesPrimer help')
