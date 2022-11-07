from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
''' If the user isn’t logged in, redirect to settings.LOGIN_URL, passing the current absolute path in the query string.
    If the user is logged in, execute the view normally. The view code is free to assume the user is logged in. '''
from django.db import IntegrityError
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from . import models
from .forms import ListingForm, BidForm, CommentForm
from .models import User, Listing, Bid, Comment


def index(request):
    listing = Listing.objects.all().filter(status=Listing.ACTIVE).order_by('-listing_date')
    if request.user.is_authenticated:
        user_watch = User.objects.get(pk=int(request.user.id)).watchlist.all()
        return render(request, "auctions/index.html", {"listing": listing, "watchlist": user_watch})
    return render(request, "auctions/index.html", {"listing": listing})


@login_required(login_url="/login")
def create_listing(request):
    form = ListingForm(request.POST)
    form.owner = request.user
    if request.method == "POST":
        if form.is_valid():
            try:
                new_listing = form.save(commit=False)
                ''' If you call save() with commit=False, then it will return and object that hasn’t yet been saved to the database. In this case, it’s up to you to call save() on the resulting model instance. This is useful if you want to do custom processing on the object before saving it, or if you want to use
                one of the specialized model saving options. commit is True by default. '''
                new_listing.owner = request.user
                new_listing.save()
            except IntegrityError:
                messages.add_message(request, messages.WARNING, "Unable to add the listing.")
                return render(request, "auctions/create_listing.html", {"form": form})
            # Successfully created a Listing
            messages.add_message(request, messages.SUCCESS, "Success! Your listing has been created.")
            return HttpResponseRedirect(reverse("index"))
        # Form is not valid
        messages.add_message(request, messages.WARNING, "Something went wrong. Please try again.")
        return render(request, "auctions/create_listing.html", {"form": form})
    # Default is to render the create_listing form
    return render(request, 'auctions/create_listing.html', {"form": ListingForm()})


def listing(request, listing_id):
    list_args = {"listing_id": listing_id, "user_id": request.user.id, "bid_form": None, "cmt_form": None}
    return render(request, "auctions/listing.html", _get_listing_dict(list_args))


def _get_listing_dict(list_args):
    listing_id = list_args["listing_id"]
    user_id = list_args["user_id"]
    user_watchlist = None

    cmt_form = list_args["cmt_form"]
    if cmt_form is None:
        cmt_form = CommentForm()

    bid_form = list_args["bid_form"]
    if bid_form is None:
        bid_form = BidForm()

    try:
        listing = Listing.objects.get(pk=listing_id)
        comments = Comment.objects.get_queryset().filter(listing=listing)
        comment_count = Comment.objects.get_queryset().filter(listing=listing).count()
        bids = Bid.objects.get_queryset().filter(listing=listing).count()
        if user_id:
            user_watchlist = User.objects.get(pk=int(user_id)).watchlist.all()
    except Listing.DoesNotExist:
        raise Http404("Listing not found.")
    except User.DoesNotExist:
        raise Http404("User not found.")
    return {
        "listing": listing,
        "bid_form": bid_form,
        "bids": bids,
        "comments": comments,
        "comment_count": comment_count,
        "cmt_form": cmt_form,
        "watchlist": user_watchlist
    }


@login_required(login_url="/login")
def watchlist(request, user_id):
    try:
        user_watchlist = User.objects.get(pk=int(user_id)).watchlist.all()
    except User.DoesNotExist:
        raise Http404("User not found")
    return render(request, "auctions/all_listing.html", {
        "listings": user_watchlist,
        "watchlist": user_watchlist,
        "category": Listing.CATEGORY_CHOICES
    })


@require_http_methods(["POST"])
@login_required(login_url="/login")
def add_watchlist(request):
    try:
        user = User.objects.get(pk=int(request.user.id))
        selected_listing = Listing.objects.get(pk=int(request.POST["listing_id"]))
        user.watchlist.add(selected_listing)
    except User.DoesNotExist:
        raise Http404("User not found.")
    except Listing.DoesNotExist:
        raise Http404("Listing not found.")
    messages.add_message(request, messages.SUCCESS, "Success! Added to the watchlist.")
    return HttpResponseRedirect(reverse("listing", args=(selected_listing.id,)))


@require_http_methods(["POST"])
@login_required(login_url="/login")
def remove_watchlist(request):
    try:
        user = User.objects.get(pk=int(request.user.id))
        selected_listing = Listing.objects.get(pk=int(request.POST["listing_id"]))
        user.watchlist.remove(selected_listing)
    except User.DoesNotExist:
        raise Http404("User not found.")
    except Listing.DoesNotExist:
        raise Http404("Listing not found.")
    messages.add_message(request, messages.SUCCESS, "Success, removed from the watchlist!")
    return HttpResponseRedirect(reverse("listing", args=(selected_listing.id,)))


@require_http_methods(["POST"])
@login_required(login_url="/login")
def place_bid(request):
    top_bid = 0
    try:
        bid_listing = Listing.objects.get(pk=int(request.POST["listing_id"]))
    except Listing.DoesNotExist:
        raise Http404("Listing not found.")

    if bid_listing.top_bid():
        top_bid = int(bid_listing.top_bid().bid)
    # BidForm will validate the new bid against top_bid and min_bid data provided to BidForm constructor.
    form = BidForm(request.POST, min_bid=int(bid_listing.min_bid), top_bid=top_bid)
    if form.is_valid():
        try:
            # Create a BidModel from the form, add Listing and User data before saving the Bid
            new_bid = form.save(commit=False)
            new_bid.listing = bid_listing
            new_bid.owner = request.user
            new_bid.save()
        except IntegrityError:
            messages.add_message(request, messages.WARNING, "Unable to place your bid.")
            return HttpResponseRedirect(reverse("listing", args=(bid_listing.id,)))
        # Saving the bid was successful
        messages.add_message(request, messages.SUCCESS, "Your bid was successful.")
        return HttpResponseRedirect(reverse("listing", args=(bid_listing.id,)))
    # Form is invalid.
    messages.add_message(request, messages.WARNING, "Unable to process your bid.")
    # On error, return the dict needed for listing page and the bound form with invalid data.
    list_args = {"bid_form": form,
                 "cmt_form": None,
                 "listing_id": request.POST["listing_id"],
                 "user_id": request.user.id}
    return render(request, "auctions/listing.html", _get_listing_dict(list_args))


@login_required(login_url="/login")
def add_comment(request):
    form = CommentForm(request.POST)
    form.owner = request.user
    if request.method == "POST":
        if form.is_valid():
            try:
                cmt_listing = Listing.objects.get(pk=int(request.POST["listing_id"]))
                new_cmt = form.save(commit=False)
                new_cmt.listing = cmt_listing
                new_cmt.owner = request.user
                new_cmt.save()
            except IntegrityError:
                messages.add_message(request, messages.WARNING, "Unable to post a comment. Try again")
                return HttpResponseRedirect(reverse("listing", args=(cmt_listing.id,)))
            except Listing.DoesNotExist:
                raise Http404("Listing Not Found")
            # Comment successfully added
            messages.add_message(request, messages.SUCCESS, "Comment successfully posted")
            return HttpResponseRedirect(reverse("listing", args=(cmt_listing.id,)))
        # if form is not valid
        messages.add_message(request, messages.WARNING, "Unable to post a comment")

        list_args = {"bid_form": None,
                     "cmt_form": form,
                     "listing_id": request.POST["listing_id"],
                     "user_id": request.user.id
                     }
        return render(request, 'auctions/listing.html', {_get_listing_dict(list_args)})


@require_http_methods(["POST"])
@login_required(login_url="/login")
def close_listing(request):
    try:
        status_listing = Listing.objects.get(pk=int(request.POST["listing_id"]))
        status_listing.status = Listing.CLOSED
        status_listing.save()
    except Listing.DoesNotExist:
        raise Http404("Listing not found")
    messages.add_message(request, messages.INFO, "Auction is closed")
    return HttpResponseRedirect(reverse("listing", args=(status_listing.id,)))


@login_required(login_url="/login")
def my_listing(request):
    my_listing = Listing.objects.all().filter(owner=request.user.id).order_by('-listing_date')
    try:
        user_watch = User.objects.get(pk=int(request.user.id)).watchlist.all()
    except User.DoesNotExist:
        raise Http404("User not found")
    return render(request, "auctions/my_listing.html", {
        "listings": my_listing,
        "watchlist": user_watch,
        "category": Listing.CATEGORY_CHOICES
    })


def all_listing(request):
    all_listing = Listing.objects.all().order_by('-listing_date')
    if request.user.is_authenticated:
        try:
            user_watch = User.objects.get(pk=int(request.user.id)).watchlist.all()
        except User.DoesNotExist:
            raise Http404("User not found")
        return render(request, "auctions/all_listing.html", {
            "listings": all_listing,
            "watchlist": user_watch,
            "category": Listing.CATEGORY_CHOICES
        })
    return render(request, "auctions/all_listing.html", {
        "listings": all_listing,
        "category": Listing.CATEGORY_CHOICES
    })


def category_sort(request, category):
    listing = Listing.objects.all().filter(category=category, status=Listing.ACTIVE).order_by('-listing_date')
    return render(request, 'auctions/all_listing.html', {
        "listings": listing,
        "category": Listing.CATEGORY_CHOICES
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
