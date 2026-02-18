from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.leads.models import Lead
from apps.leads.services import LeadService
from .serializers import LeadSerializer, LeadSummarySerializer

class LeadViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing leads.
    """
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Gym Isolation
        if hasattr(self.request.user, 'gym') and self.request.user.gym:
             return Lead.objects.filter(gym=self.request.user.gym).order_by('-created_at')
        return Lead.objects.none()

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'gym') and self.request.user.gym:
            serializer.save(gym=self.request.user.gym)
        else:
             # This should ideally be handled by permission/validation, but safe fallback
             pass

    @action(detail=True, methods=['post'])
    def convert(self, request, pk=None):
        """
        Convert a lead to a member.
        """
        lead = self.get_object()
        
        member, error = LeadService.convert_lead(lead, converted_by=request.user)
        
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({
            'message': 'Lead converted successfully',
            'member_id': member.id,
            'status': 'converted'
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='bulk-convert')
    def bulk_convert(self, request):
        """
        Convert multiple leads to members.
        Expects: { "ids": [1, 2, 3] }
        """
        lead_ids = request.data.get('ids', [])
        if not lead_ids:
            return Response({'error': 'No lead IDs provided'}, status=status.HTTP_400_BAD_REQUEST)

        results = LeadService.bulk_convert(lead_ids, request.user)
        
        return Response(results, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get lead summary statistics.
        """
        if not hasattr(request.user, 'gym') or not request.user.gym:
            return Response({'error': 'User not associated with a gym'}, status=status.HTTP_400_BAD_REQUEST)

        stats = LeadService.get_lead_summary(request.user.gym)
        serializer = LeadSummarySerializer(stats)
        return Response(serializer.data)
