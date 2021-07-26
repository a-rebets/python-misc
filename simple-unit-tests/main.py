import pytest

accepted_methods = ['GET','HEAD','POST','PUT','DELETE','TRACE','OPTIONS','CONNECT','PATCH']
accepted_protocols = ['HTTP1.0', 'HTTP1.1', 'HTTP2.0']

class Request:
  def __init__(self, method, path, protocol):
    self.method = method
    self.path = path
    self.protocol = protocol

  def get_method(self):
    return self.method

  def get_path(self):
    return self.path
  
  def get_protocol(self):
    return self.protocol
  
  def __str__(self):
    return 'Request[method - %s, path - %s, protocol - %s]'%(self.method, self.path, self.protocol)

  def __eq__(self, other):
    if (isinstance(other, Request)):
      return self.method == other.method and self.path == other.path and self.protocol == other.protocol

class BadRequestTypeError(Exception):
  pass

class BadHTTPVersion(Exception):
  pass

def reqstr2obj(request_string):
  if not isinstance(request_string, str):
    raise TypeError
  req = request_string.split(' ')
  try:
    if req[0] not in accepted_methods:
      raise BadRequestTypeError
    if req[2] not in accepted_protocols:
      raise BadHTTPVersion
    if not req[1].startswith('/'):
      raise ValueError('Path must start with /')

    return Request(req[0], req[1], req[2])
  except IndexError:
    return None

class TestClass:
  def test_one(self):
    with pytest.raises(TypeError):
      reqstr2obj(7)

  def test_two(self):
    assert isinstance(reqstr2obj('GET / HTTP1.1'), Request)

  def test_three(self):
    test_req = 'GET / HTTP1.1'.split(' ')
    obj = reqstr2obj('GET / HTTP1.1')
    assert (obj.get_method(), obj.get_path(), obj.get_protocol()) == (test_req[0], test_req[1], test_req[2])
    
  @pytest.mark.parametrize('arg, output', [
    ('POST / HTTP1.0', Request('POST', '/', 'HTTP1.0')),
    ('GET /usr/home/somefile HTTP1.1', Request('GET', '/usr/home/somefile', 'HTTP1.1'))
  ])
  def test_four(self, arg, output):
    assert reqstr2obj(arg) == output

  def test_five(self):
     assert reqstr2obj('PATCH /') is None

  def test_six(self):
    with pytest.raises(BadRequestTypeError):
      reqstr2obj('DOWNLOAD /movie.mp4 HTTP1.1')
  
  def test_seven(self):
    with pytest.raises(BadHTTPVersion):
      reqstr2obj('GET /test/file.txt HTTP2.1')
  
  def test_eight(self):
    with pytest.raises(ValueError) as e:
      reqstr2obj('PUT image.jpg HTTP1.0')
      assert str(e.value) == 'Path must start with /'