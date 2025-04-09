from django.core.management.base import BaseCommand
from documents.models import DocumentCategory


class Command(BaseCommand):
    help = 'Creates default document categories if they do not exist'

    def handle(self, *args, **kwargs):
        # Define default categories with descriptions
        default_categories = [
            {
                'name': 'Cleaning Procedures',
                'description': 'Standard operating procedures for different cleaning tasks and environments.'
            },
            {
                'name': 'Training Materials',
                'description': 'Documents used for training cleaners and staff on proper techniques and standards.'
            },
            {
                'name': 'Safety Documentation',
                'description': 'Safety guidelines, MSDS sheets, hazard information, and emergency procedures.'
            },
            {
                'name': 'Contracts & Legal',
                'description': 'Templates and examples of service contracts, agreements, and legal documents.'
            },
            {
                'name': 'Equipment Manuals',
                'description': 'User manuals and maintenance guides for cleaning equipment and machinery.'
            },
            {
                'name': 'Cleaning Products',
                'description': 'Information about cleaning solutions, chemicals, and their proper usage.'
            },
            {
                'name': 'Quality Control',
                'description': 'Checklists, inspection forms, and quality assurance documentation.'
            },
            {
                'name': 'Customer Service',
                'description': 'Guidelines for customer interactions, complaint handling, and service excellence.'
            },
            {
                'name': 'Certification Documents',
                'description': 'Industry certifications, licenses, and professional qualification documents.'
            },
            {
                'name': 'Schedule Templates',
                'description': 'Templates for creating cleaning schedules and rotation plans.'
            },
        ]
        
        # Create categories if they don't exist
        created_count = 0
        existing_count = 0
        
        for category_data in default_categories:
            category, created = DocumentCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
            else:
                existing_count += 1
                self.stdout.write(self.style.WARNING(f'Category already exists: {category.name}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'Categories created: {created_count}, already existing: {existing_count}'
        ))