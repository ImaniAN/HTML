import cups

class PrintService:
    def __init__(self):
        self.conn = cups.Connection()
        self.printers = self.conn.getPrinters()

    def get_printers(self):
        return list(self.printers.keys())

    def submit_print_job(self, user_id, file_path, printer_name, options=None):
        try:
            if not options:
                options = {'media': 'A4', 'copies': '1'}
            job_id = self.conn.printFile(
                printer_name,
                file_path,
                "Print Job from " + str(user_id),
                options
            )
            return job_id
        except Exception as e:
            logging.error(f"Print error: {e}")
            return None

    def get_job_status(self, job_id):
        try:
            jobs = self.conn.getJobs()
            return jobs.get(job_id, {}).get('state', 'unknown')
        except Exception as e:
            logging.error(f"Job status error: {e}")
            return 'error'
