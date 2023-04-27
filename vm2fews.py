#!/usr/bin/python3
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
from typing import Dict, List, NamedTuple, Optional


class Config(NamedTuple):
    """Configurazione ottenuta da sys.argv"""

    dataset: str
    start_date: datetime
    end_date: datetime
    step: timedelta
    arkiweb_url: str
    indent: List[str]


class DataRecord(NamedTuple):
    reftime: datetime
    # Non dobbiamo fare calcoli, quindi possiamo evitare il parsing del valore
    # e memorizzarlo come str, in questo modo evitiamo errori di arrotondamento.
    value: str
    is_good: bool


class Vm2Location(NamedTuple):
    vm2_station_id: int
    vm2_variable_id: int


class FewsSeriesParameters(NamedTuple):
    units: str
    type: str


# FIXME: units dovrebbe essere presa da meteozen (vm2_unit)
# FIXME: type dovrebbe essere aggiunta a meteozen
FEWS_SERIES_PARAMETERS = {
    158: FewsSeriesParameters(units="C", type="instantaneous"),
    160: FewsSeriesParameters(units="mm", type="accumulation"),
    161: FewsSeriesParameters(units="m", type="instantaneous"),
    162: FewsSeriesParameters(units="cm", type="instantaneous"),
}
"""Mapping da vm2_variable_id a FewsSeriesParameters"""


def write(what: str) -> None:
    """Usata per evitare righe vuote nell'xml d'uscita"""
    print(what, end="")


def print_fewsxml_header():
    write(
        '''<TimeSeries xmlns="http://www.wldelft.nl/fews/PI"'''
        ''' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'''
        """ xsi:schemaLocation="http://www.wldelft.nl/fews/PI"""
        ''' http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseries.xsd"'''
        ''' version="1.19"'''
        """ xmlns:fs="http://www.wldelft.nl/fews/fs">"""
    )


def print_fewsxml_series(
    cfg: Config,
    location: Vm2Location,
    data: List[DataRecord],
):
    def date(dt: datetime):
        return dt.strftime("%Y-%m-%d")

    def time(dt: datetime):
        return dt.strftime("%H:%M:%S")

    series_parameters = FEWS_SERIES_PARAMETERS[location.vm2_variable_id]
    write(f"""{cfg.indent[0]}<series>""")
    write(
        f"""{cfg.indent[1]}<header>"""
        f"""{cfg.indent[2]}<type>{ series_parameters.type }</type>"""
        f"""{cfg.indent[2]}<locationId>{ location.vm2_station_id }</locationId>"""
        f"""{cfg.indent[2]}<parameterId>{ location.vm2_variable_id }</parameterId>"""
        f"""{cfg.indent[2]}<timeStep unit="second" multiplier="{ int(cfg.step.total_seconds()) }"/>"""
        f"""{cfg.indent[2]}<startDate date="{ date(cfg.start_date) }" time="{ time(cfg.start_date) }"/>"""
        f"""{cfg.indent[2]}<endDate date="{ date(cfg.end_date) }" time="{ time(cfg.end_date) }"/>"""
        f"""{cfg.indent[2]}<units>{ series_parameters.units }</units>"""
        f"""{cfg.indent[1]}</header>"""
    )
    for rec in data:
        write(
            f"""{cfg.indent[1]}<event"""
            f''' date="{ date(rec.reftime) }"'''
            f''' time="{ time(rec.reftime) }"'''
            f''' value="{ rec.value }"'''
            f"""{ '' if rec.is_good else ' flag="6"' }/>"""
        )
    write(f"""{cfg.indent[0]}</series>""")


def print_fewsxml_footer():
    write("""</TimeSeries>""")


def url_open(url: str):
    """
    Ritorna la risposta a GET url, gestendo anche l'autenticazione di tipo
    BasicAuth se contiene un username. Per garantire la chiusura, usare così:

        with url_open(url) as response:
            print(response.read().decode('utf-8'))
    """
    from urllib import parse, request

    urls = parse.urlsplit(url)
    port = f":{urls.port}" if urls.port else ""
    netloc = (urls.hostname if urls.hostname else "") + port
    parts = (urls.scheme, netloc, urls.path, urls.query, urls.fragment)
    unauth_url = parse.urlunsplit(parts)
    if urls.username:
        password_mgr = request.HTTPPasswordMgrWithPriorAuth()
        password_mgr.add_password(
            "", unauth_url, urls.username, urls.password or "", is_authenticated=True
        )
        handler = request.HTTPBasicAuthHandler(password_mgr)
        opener = request.build_opener(handler)
    else:
        opener = request.build_opener()
    return opener.open(unauth_url)


def datetime_toarkimetreftime(dt: datetime, step: Optional[timedelta] = None):
    arkistep = f"%{int(step.total_seconds())}s" if step else ""
    return dt.strftime("%Y-%m-%d %H:%M") + arkistep


def arkiweb_build_url(cfg: Config):
    from urllib import parse

    products = " or VM2,".join(map(str, FEWS_SERIES_PARAMETERS.keys()))
    start = datetime_toarkimetreftime(cfg.start_date, cfg.step)
    end = datetime_toarkimetreftime(cfg.end_date)
    query = parse.quote_plus(f"reftime:>={start},<={end};product:VM2,{products}")
    return f"{cfg.arkiweb_url}/data" f"?datasets[]={cfg.dataset}" f"&query={query}"


def arkiweb_get(cfg: Config):
    from urllib.error import URLError

    outpath = Path(f"{cfg.dataset}.vm2")
    url = arkiweb_build_url(cfg)
    try:
        with open(outpath, "wb") as out, url_open(url) as response:
            out.write(response.read())
    except URLError as e:
        raise RuntimeError(f"Cannot GET {url}") from e
    return outpath


def datetime_fromisoutcformat(isoutc: str) -> datetime:
    """
    Parse di datetime in formato ISO 8601 con timezone 'Z'.
    TODO: Questo serve per compatibilità con python-3.6.
    In python-3.7 si può usare "%z" ed accettare qualsiasi
    timezone (ricordandosi poi di cambiarla in UTC)
    """
    return datetime.strptime(isoutc, "%Y-%m-%dT%H:%M:%SZ")


def datetime_floor(dt: datetime, step: timedelta):
    """Arrotonda un datetime allo step precedente"""
    from math import floor

    seconds = step.total_seconds()
    return datetime.fromtimestamp(
        seconds * floor(dt.timestamp() / seconds), tz=dt.tzinfo
    )


def parse_timedelta(td: str):
    qtas, um = td[:-1], td[-1]
    if qtas.isdecimal():
        qta = int(qtas)
        if um == "h":
            return timedelta(hours=qta)
        if um == "m":
            return timedelta(minutes=qta)
        if um == "s":
            return timedelta(seconds=qta)
    raise Exception(
        f"timedelta non valido {td}."
        " Formati accettati: Xh (= X ore), Xm (= X minuti), Xs (= X secondi)"
    )


def get_config():
    """Ricava la configurazione dagli argomenti"""
    import argparse

    default_hours = 2
    default_arkiweb_url_file = Path("arkiweb_url.txt")
    parser = argparse.ArgumentParser(
        description="Scarica dati da Arkiweb e li converte in XML per FEWS.",
        epilog="ATTENZIONE: la URL da cui scaricare i dati deve essere scritta in"
        f" un file (default: {default_arkiweb_url_file}). Questo evita di passare"
        " utente e password da linea di comando.",
    )
    parser.add_argument(
        "dataset", help="Nome della rete delle stazioni di cui si vogliono i dati."
    )
    parser.add_argument(
        "--hours",
        type=int,
        help="Quante ore di dati scaricare partendo da '--start_date' o finendo con '--end_date'."
        f" Alternativa a '--start_date' o '--end_date'. Default: {default_hours}.",
    )
    parser.add_argument(
        "--start_date",
        "-s",
        type=datetime_fromisoutcformat,
        help="Data e ora di inizio in formato ISO 8601 con timezone fissata a Z (es. 2022-12-23T09:00:00Z)."
        " Viene arrotondato allo step precedente.",
    )
    parser.add_argument(
        "--end_date",
        "-e",
        type=datetime_fromisoutcformat,
        help="Data e ora di fine in formato ISO 8601 con timezone fissata a Z (es. 2022-12-23T09:00:00Z)."
        " Viene arrotondato allo step precedente. Default: ora attuale.",
    )
    parser.add_argument(
        "--step",
        type=parse_timedelta,
        default=timedelta(hours=1),
        help="Periodicità dei dati scaricati espressa in ore (h), minuti (m) o secondi (s). Default: 1h",
    )
    parser.add_argument(
        "--arkiweb_url_file",
        type=Path,
        default=default_arkiweb_url_file,
        help="File contenente la URL di arkiweb (es. di URL: https://USER:PASSWORD@simc.arpae.it/services/arkiweb)."
        f" Default: {default_arkiweb_url_file}",
    )
    parser.add_argument(
        "--indent", action="store_true", help="Genera un output indentato"
    )
    args = parser.parse_args()
    if args.start_date and args.end_date:
        if args.hours:
            raise Exception(
                "Con '--hours', usare solo '--start_date' oppure '--end_date'"
            )
        start_date = datetime_floor(args.start_date, args.step)
        end_date = datetime_floor(args.end_date, args.step)
    else:
        # Manca start_date e/o end_date: usiamo hours
        hours = timedelta(hours=args.hours or default_hours)
        if args.start_date:
            start_date = datetime_floor(args.start_date, args.step)
            end_date = start_date + hours
        else:
            # Manca start_date: usiamo end_date (con default = now)
            end_date = datetime_floor(
                args.end_date or datetime.now(timezone.utc), args.step
            )
            start_date = end_date - hours
    if start_date > end_date:
        raise Exception("Intervallo di date non valido: start_date > end_date")
    if not args.arkiweb_url_file.exists():
        raise Exception(f"Il file {args.arkiweb_url_file} non esiste")
    with open(args.arkiweb_url_file, encoding="utf-8") as fp:
        arkiweb_url = fp.read().strip()
    # Per le nostre esigenze, è sufficiente un'implementazione di indent primitiva:
    # un array di rientri, uno per ogni livello di indentazione.
    if args.indent:
        # "\n" all'inizio fa andare a capo prima di indentare
        indent = ["\n", "\n  ", "\n    "]
    else:
        # niente indentazione e niente a capo
        indent = ["", "", ""]
    return Config(
        dataset=args.dataset,
        start_date=start_date,
        end_date=end_date,
        step=args.step,
        arkiweb_url=arkiweb_url,
        indent=indent,
    )


def parse_vm2(vm2in: Path):
    def parse_reftime(rt: str):
        """Crea un datetime dal formato YYYYmmddHHMM[SS]."""
        # Nel VM2 le due cifre dei secondi sono facoltative.
        # Usare datetime.strptime() è più complicato perché il padding a due cifre
        # per minuti e secondi è facoltativo quindi, se mancano i secondi, legge
        # le due cifre dei minuti (MM) come minuti e secondi.
        return datetime(
            int(rt[0:4]),
            int(rt[4:6]),
            int(rt[6:8]),
            int(rt[8:10]),
            int(rt[10:12]),
            # secondi = 0 se assenti
            int(rt[12:14] or 0),
        )

    all_data: Dict[Vm2Location, List[DataRecord]] = {}
    with open(vm2in, encoding="utf-8", newline="") as fp:
        for row in csv.reader(fp):
            location = Vm2Location(int(row[1]), int(row[2]))
            location_data = all_data.setdefault(location, [])
            flags = row[6]
            location_data.append(
                DataRecord(
                    reftime=parse_reftime(row[0]),
                    # evito la conversione in float per ridurre errori di arrotondamento
                    value=row[4] if flags.startswith("2") else row[3],
                    is_good=not (flags.startswith("1") or flags[1:3] == "54"),
                ),
            )
    return all_data


def main() -> int:
    cfg = get_config()
    print_fewsxml_header()
    for location, location_data in parse_vm2(arkiweb_get(cfg)).items():
        print_fewsxml_series(cfg, location, location_data)
    print_fewsxml_footer()
    return 0


if __name__ == "__main__":
    sys.exit(main())
