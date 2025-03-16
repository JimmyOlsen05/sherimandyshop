from django import forms
from .models import ReviewRating


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={
            'class': 'rating-input',
            'style': 'display: none;'
        })
    )
    
    review = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Share your experience with this product...',
            'rows': 4,
            'style': 'resize: none; border-radius: 10px;'
        }),
        required=True,
        min_length=10,
        max_length=500
    )

    class Meta:
        model = ReviewRating
        fields = ['review', 'rating']

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if rating < 1 or rating > 5:
            raise forms.ValidationError("Rating must be between 1 and 5 stars")
        return rating

    def clean_review(self):
        review = self.cleaned_data.get('review')
        if len(review.strip()) < 10:
            raise forms.ValidationError("Review must be at least 10 characters long")
        return review