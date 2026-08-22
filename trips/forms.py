from django import forms
from .models import Trip, TripStop, ScheduledActivity, TripExpense, TripReview, TripComment

class TripCreateForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = Trip
        fields = ['title', 'description', 'start_date', 'end_date', 'estimated_budget', 'currency', 'travel_style', 'is_public', 'cover_image', 'cover_image_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 8 Days Magical Kashmir & Himachal Mountain Odyssey'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What are your highlights, mountain passes, or heritage spots for this journey?'}),
            'estimated_budget': forms.NumberInput(attrs={'class': 'form-control', 'step': '100.00', 'placeholder': '35000.00'}),
            'currency': forms.Select(choices=Trip.CURRENCY_CHOICES, attrs={'class': 'form-select'}),
            'travel_style': forms.Select(attrs={'class': 'form-select'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': 'checked'}),
            'cover_image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://images.unsplash.com/...'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("Trip title is required.")
        return title

    def clean_estimated_budget(self):
        budget = self.cleaned_data.get('estimated_budget')
        if budget is not None and budget <= 0:
            raise forms.ValidationError("Estimated budget must be greater than zero.")
        return budget

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "End date cannot be earlier than start date.")
        return cleaned_data


class TripStopForm(forms.ModelForm):
    arrival_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    departure_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = TripStop
        fields = ['city', 'arrival_date', 'departure_date', 'accommodation_name', 'stay_cost', 'transport_to_stop_type', 'transport_cost', 'notes']
        widgets = {
            'city': forms.Select(attrs={'class': 'form-select'}),
            'accommodation_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hotel / Houseboat / Resort / Homestay name'}),
            'stay_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '100.00', 'placeholder': '0.00'}),
            'transport_to_stop_type': forms.Select(attrs={'class': 'form-select'}),
            'transport_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '100.00', 'placeholder': '0.00'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Check-in details, Vande Bharat train or flight info...'}),
        }

    def clean_stay_cost(self):
        stay_cost = self.cleaned_data.get('stay_cost')
        if stay_cost is not None and stay_cost < 0:
            raise forms.ValidationError("Stay cost cannot be negative.")
        return stay_cost

    def clean_transport_cost(self):
        transport_cost = self.cleaned_data.get('transport_cost')
        if transport_cost is not None and transport_cost < 0:
            raise forms.ValidationError("Transport cost cannot be negative.")
        return transport_cost

    def clean(self):
        cleaned_data = super().clean()
        arr = cleaned_data.get('arrival_date')
        dep = cleaned_data.get('departure_date')
        if arr and dep and dep < arr:
            self.add_error('departure_date', "Departure date must be on or after arrival date.")
        return cleaned_data


class ScheduledActivityForm(forms.ModelForm):
    scheduled_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    start_time = forms.TimeField(required=False, widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}))

    class Meta:
        model = ScheduledActivity
        fields = ['stop', 'activity', 'title', 'category', 'scheduled_date', 'start_time', 'duration_minutes', 'cost', 'location', 'notes']
        widgets = {
            'stop': forms.Select(attrs={'class': 'form-select'}),
            'activity': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Shikara Ride on Dal Lake at Sunset'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'step': '15', 'placeholder': '120'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '50.00', 'placeholder': '500.00'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Meeting point, ghat, or exact location'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Entry tickets, permit info, dress code...'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("Activity title is required.")
        return title

    def clean_cost(self):
        cost = self.cleaned_data.get('cost')
        if cost is not None and cost < 0:
            raise forms.ValidationError("Activity cost cannot be negative.")
        return cost

    def clean_duration_minutes(self):
        duration = self.cleaned_data.get('duration_minutes')
        if duration is not None and duration <= 0:
            raise forms.ValidationError("Duration must be at least 1 minute.")
        return duration


class TripExpenseForm(forms.ModelForm):
    expense_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = TripExpense
        fields = ['category', 'title', 'amount', 'expense_date', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Authentic Kathiyawadi Thali Lunch'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '50.00', 'placeholder': '450.00'}),
            'notes': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UPI / Card / Cash note...'}),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("Expense title is required.")
        return title

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError("Expense amount must be greater than zero.")
        return amount


class TripReviewForm(forms.ModelForm):
    class Meta:
        model = TripReview
        fields = ['rating', 'title', 'comment']
        widgets = {
            'rating': forms.Select(choices=[(5, '⭐⭐⭐⭐⭐ (5/5) - Outstanding Journey!'), (4, '⭐⭐⭐⭐ (4/5) - Great Itinerary'), (3, '⭐⭐⭐ (3/5) - Good Plan'), (2, '⭐⭐ (2/5) - Needs Adjustments'), (1, '⭐ (1/5) - Poor')], attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Headline for your review...'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share what made this itinerary exciting, scenic, or practical...'}),
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '').strip()
        if not comment:
            raise forms.ValidationError("Review comment cannot be blank.")
        return comment


class TripCommentForm(forms.ModelForm):
    class Meta:
        model = TripComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ask a question or share a local tip for this itinerary...'}),
        }

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise forms.ValidationError("Comment cannot be blank.")
        return content
