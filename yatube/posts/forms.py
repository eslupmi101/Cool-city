from django import forms

from .models import Comment, Group, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_group(self):
        data = self.cleaned_data['group']
        group = Group.objects.filter(title=data)
        if not group.exists() and data:
            raise forms.ValidationError("Группы с названием "
                                        f"'{data}' не существует")
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )
