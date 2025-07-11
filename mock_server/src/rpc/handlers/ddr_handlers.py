"""
DDR (Data Dictionary Request) RPC handlers
Requires ALLOW_DDR flag for access
"""

from src.rpc.models import Parameter


class DDRHandlers:
    """Handlers for DDR RPCs - Data Dictionary access"""

    @staticmethod
    def handle_ddr_lister(parameters: list[Parameter]) -> str:
        """
        Handle DDR LISTER - List data dictionary entries
        Returns delimited string format

        Note: This is a simplified mock. Real DDR LISTER has complex parameter structure
        for querying FileMan data dictionary.
        """
        # Get parameters
        file_number = ""

        if parameters:
            if len(parameters) > 0:
                param_value = parameters[0].get_value()
                if isinstance(param_value, str):
                    file_number = param_value

            if len(parameters) > 1:
                param_value = parameters[1].get_value()
                if isinstance(param_value, str):
                    pass

            if len(parameters) > 2:
                param_value = parameters[2].get_value()
                if isinstance(param_value, str):
                    pass

        # Mock some common file definitions
        if file_number == "2":  # Patient file
            return (
                "FILE #2^PATIENT^1^200000\n"
                ".01^NAME^FREE TEXT^30^R\n"
                ".02^SEX^SET^1^R\n"
                ".03^DATE OF BIRTH^DATE^8^R\n"
                ".09^SOCIAL SECURITY NUMBER^FREE TEXT^9^\n"
                ".301^SERVICE CONNECTED?^SET^1^\n"
                ".302^SERVICE CONNECTED PERCENTAGE^NUMERIC^3^\n"
                "1901^ELIGIBILITY STATUS^POINTER^10^"
            )
        elif file_number == "200":  # New Person file
            return (
                "FILE #200^NEW PERSON^1^50000\n"
                ".01^NAME^FREE TEXT^30^R\n"
                "8^TITLE^FREE TEXT^30^\n"
                "29^SERVICE/SECTION^POINTER^49^\n"
                ".131^PERSON CLASS^MULTIPLE^200.05^\n"
                ".132^DEA#^FREE TEXT^15^\n"
                "53.1^ELECTRONIC SIGNATURE^MUMPS^20^"
            )
        elif file_number == "44":  # Hospital Location file
            return (
                "FILE #44^HOSPITAL LOCATION^1^10000\n"
                ".01^NAME^FREE TEXT^30^R\n"
                "2^ABBREVIATION^FREE TEXT^6^\n"
                "3^TYPE^SET^1^R\n"
                "9^SERVICE^POINTER^49^\n"
                "10^PHYSICAL LOCATION^FREE TEXT^20^\n"
                "99^CLINIC STOP CODE^POINTER^40.7^"
            )
        else:
            # Generic response for unknown files
            return f"FILE #{file_number}^UNKNOWN FILE^0^0\nNo fields found"

    @staticmethod
    def handle_ddr_find(parameters: list[Parameter]) -> str:
        """
        Handle DDR FIND - Find entries in a file
        Returns delimited string format
        """
        # Get parameters
        file_number = ""
        search_value = ""

        if parameters:
            if len(parameters) > 0:
                param_value = parameters[0].get_value()
                if isinstance(param_value, str):
                    file_number = param_value

            if len(parameters) > 1:
                param_value = parameters[1].get_value()
                if isinstance(param_value, str):
                    search_value = param_value.upper()

            if len(parameters) > 2:
                param_value = parameters[2].get_value()
                if isinstance(param_value, str):
                    pass

        # Mock search results
        results = []

        if file_number == "2" and search_value:  # Patient file search
            # Search our test patients
            test_patients = [
                ("100022", "ANDERSON,JAMES ROBERT"),
                ("100023", "MARTINEZ,MARIA ELENA"),
                ("100024", "THOMPSON,MICHAEL DAVID"),
                ("100025", "WILLIAMS,ROBERT EARL"),
                ("100026", "JOHNSON,DAVID WAYNE"),
                ("100027", "DAVIS,JENNIFER LYNN"),
                ("100028", "WILSON,GEORGE HENRY"),
                ("100029", "GARCIA,ANTONIO JOSE"),
            ]

            for ien, name in test_patients:
                if search_value in name:
                    results.append(f"{ien}^{name}")

        elif file_number == "200" and search_value:  # Provider search
            test_providers = [
                ("10000000219", "PROVIDER,TEST"),
                ("10000000220", "WILLIAMS,PATRICIA L"),
                ("10000000221", "SMITH,JENNIFER A"),
                ("10000000222", "JONES,MARK R"),
                ("10000000223", "DAVIS,ROBERT M"),
            ]

            for ien, name in test_providers:
                if search_value in name:
                    results.append(f"{ien}^{name}")

        return "\n".join(results) if results else "No matches found"

    @staticmethod
    def handle_ddr_gets(parameters: list[Parameter]) -> str:
        """
        Handle DDR GETS - Get entry details
        Returns delimited string format with field values
        """
        # Get parameters
        file_number = ""
        ien = ""

        if parameters:
            if len(parameters) > 0:
                param_value = parameters[0].get_value()
                if isinstance(param_value, str):
                    file_number = param_value

            if len(parameters) > 1:
                param_value = parameters[1].get_value()
                if isinstance(param_value, str):
                    ien = param_value

            if len(parameters) > 2:
                param_value = parameters[2].get_value()
                if isinstance(param_value, str):
                    pass

        # Mock data retrieval
        if file_number == "2" and ien == "100022":
            return ".01^ANDERSON,JAMES ROBERT\n.02^MALE\n.03^19450315\n.09^***-**-6789\n.301^YES\n.302^70"
        elif file_number == "200" and ien == "10000000219":
            return ".01^PROVIDER,TEST\n8^PHYSICIAN\n29^MEDICINE\n53.1^**ELECTRONIC SIGNATURE ON FILE**"
        else:
            return f"Entry {ien} not found in file {file_number}"
