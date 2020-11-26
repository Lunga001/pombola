import csv
import os
from optparse import make_option

from django.core.management.base import BaseCommand

from pombola.core.models import Person, Position

from iebc_api import maybe_save, yesterday_approximate_date

data_directory = os.path.join(
    os.path.dirname(__file__), '..', '..', '2013-election-data'
)

headings = ['Place Name',
            'Place Type',
            'Race Type',
            'Old?',
            'Existing Aspirant Position ID',
            'Existing Aspirant Person ID',
            'Existing Aspirant External ID',
            'Existing Aspirant Legal Name',
            'Existing Aspirant Other Names',
            'API Normalized Name',
            'API Code',
            'Action']

class Command(BaseCommand):
    help = 'Update the database with aspirants from the IEBC website'

    option_list = BaseCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        )

    def handle_noargs(self, **options):

        csv_filename = os.path.join(data_directory, 'positions-to-end-delete-and-alternative-names.csv')

        with open(csv_filename) as fp:

            reader = csv.DictReader(fp)

            for row in reader:

                alternative_names_to_add = row['Alternative Names To Add']
                if not alternative_names_to_add:
                    continue

                try:
                    position = Position.objects.get(pk=row["Existing Aspirant Position ID"])
                except Position.DoesNotExist:
                    # Probably it's already been removed by the remove duplicates script
                    continue

                if alternative_names_to_add == '[endpos]':
                    position.end_date = yesterday_approximate_date
                    maybe_save(position, **options)
                elif alternative_names_to_add == '[delpos]':
                    if options['commit']:
                        position.delete()
                else:
                    print "------------------------------------------------------------------------"
                    print alternative_names_to_add
                    names_to_add = [an.title().strip() for an in alternative_names_to_add.split(', ')]
                    for n in names_to_add:
                        person = Person.objects.get(pk=row['Existing Aspirant Person ID'])
                        person.add_alternative_name(n)
                        maybe_save(person, **options)
