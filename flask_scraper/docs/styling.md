# Styling

## Stylesheets

#### `Common` stylesheet

Located in `app/static/styles/app.css`.

This stylesheet covers any common aspects of the website.


#### `Themed` stylesheets

Located in `app/static/styles/themes`.

The application loops through this directory and extracts the filename of each `.css` file.
This is then used in the dropdown on the `Change Theme` page accessed via the `Your Account`
section of the site.  


## Video
#### `coverr.co` video

The code for the video is in the file `app/templates/main/index.html`. As well as the js and css files provided by Coverr.co (for funtionality and positioning)

```
<div class="homepage-hero-module">
		<div class="video-container">
			<div class="title-container">
					<div class="headline">
							<!--Original logo height 80px-->
							#Main video link here
				<div style="position: absolute; bottom: 20px; left: 50%; margin-left: -19px;">
						<a class="coverr-nav-item" href="#coverrs" style="text-decoration: none;">
								<h1 class="header huge">
										<i class="huge angle down icon"></i>
								</h1>
						</a>
				</div>
		</div>
</div>
```

###

```
###
```
