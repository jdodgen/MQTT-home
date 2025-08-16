$meth=$ENV{'REQUEST_METHOD'} if defined($ENV{'REQUEST_METHOD'});
$content_length = defined($ENV{'CONTENT_LENGTH'}) ? $ENV{'CONTENT_LENGTH'} : 0;
 
 # avoid unreasonably large postings
      if (($POST_MAX > 0) && ($content_length > $POST_MAX)) {
        #discard the post, unread
        $self->cgi_error("413 Request entity too large");
        last METHOD;
      }

&& defined($ENV{'CONTENT_TYPE'})
&& $ENV{'CONTENT_TYPE'}=~m|^multipart/form-data|
$ENV{'CONTENT_TYPE'} =~ /boundary=\"?([^\";,]+)\"?/;

$query_string .= (length($query_string) ? '&' : '') . $ENV{'QUERY_STRING'} if defined $ENV{'QUERY_STRING'};
